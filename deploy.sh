#!/bin/bash
project_path="$( cd "$(dirname $BASH_SOURCE)" ; pwd -P)"
remote_host=$1
app_name="headposeestimationapp"
app_path=${project_path}/${app_name}

. ./func_util.sh
main()
{
    check_ip_addr ${remote_host}
    if [ $? -ne 0 ];then
        echo "ERROR: invalid remote_host ip, please check your input parameter."
        return 1
    fi 

    parse_presenter_altasdk_ip ${remote_host}
    parse_presenter_view_ip    
    presenter_port=`grep presenter_server_port ${project_path}/presenterserver/Head_pose/config/config.conf | awk -F '=' '{print $2}' | sed 's/[^0-9]//g'`

    echo "Use ${presenter_atlasdk_ip} to connect to Atlas DK Developerment Board..."
    sed -i "s/presenter_server_ip=[0-9.]*/presenter_server_ip=${presenter_atlasdk_ip}/g" ${project_path}/presenterserver/Head_pose/config/config.conf
    echo "Use ${presenter_view_ip} to show information in browser..."
    sed -i "s/web_server_ip=[0-9.]*/web_server_ip=${presenter_view_ip}/g" ${project_path}/presenterserver/Head_pose/config/config.conf
    echo "Finish to prepare ${app_name} presenter server ip configuration."
    
    echo "presenter_ip = '${presenter_atlasdk_ip}'" > ${app_path}/graph.py
    echo "presenter_port = ${presenter_port}" >> ${app_path}/graph.py

    face_detection_model_name=$(basename `grep face_detection_model_path ${app_path}/ConstManager.py | sed "s/'//g" | awk -F '[= ]+' '{print $2}'`)
    head_pose_model_name=$(basename `grep head_pose_model_path ${app_path}/ConstManager.py | sed "s/'//g" | awk -F '[= ]+' '{print $2}'`)
    
    echo "start deploying  ${face_detection_model_name} "
    if [[ `find ${project_path}/model -name "${face_detection_model_name}"`"X" == "X" ]];then
        echo "please input ${face_detection_model_name} into ${project_path}/model/ "
        return 1
    elif [[ $(basename `find ${project_path}/model -name "${face_detection_model_name}"`) == ${face_detection_model_name} ]];then
        upload_path ${project_path}/model "~/HIAI_PROJECTS/${app_name}"
        if [[ $? -ne 0 ]];then
            echo "deploy ${face_detection_model_name} failed"
            return 1
        fi
    fi

    echo "start deploying  ${head_pose_model_name} "
    if [[ `find ${project_path}/model -name "${head_pose_model_name}"`"X" == "X" ]];then
        echo "please input ${head_pose_model_name} into ${project_path}/model/ "
        return 1
    elif [[ $(basename `find ${project_path}/model -name "${head_pose_model_name}"`) == ${head_pose_model_name} ]];then
        upload_path ${project_path}/model "~/HIAI_PROJECTS/${app_name}"
        if [[ $? -ne 0 ]];then
            echo "deploy ${head_pose_model_name} failed"
            return 1
        fi
    fi

    echo "start deploying headposeestimationapp"
    upload_path ${app_path} "~/HIAI_PROJECTS/${app_name}"
    if [[ $? -ne 0 ]];then
        echo "deploy headposeestimationapp failed"
        return 1
    fi

    echo "start chmod +x ~/HIAI_PROJECTS/${app_name}"
    iRet=`${DDK_BIN}/IDE-daemon-client --host ${remote_host}:${remote_port} --hostcmd "chmod +x ~/HIAI_PROJECTS/${app_name}"`
    if [[ $? -ne 0 ]];then
        echo "ERROR: change excution mode ${remote_host}:~/HIAI_PROJECTS/${app_name}/* failed, please check /var/dlog for details."
        return 1
    fi
    echo "deploy finished"
}
main
