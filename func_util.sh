#!/bin/bash 

remote_port="22118"
DDK_BIN="$DDK_HOME/uihost/bin"



# ************************check remote file****************************************
# Description:  upload a file
# $1: remote file(relative ~/xxxxx)
# ******************************************************************************
function check_remote_file()
{
    filePath=$1
    if [ ! -n ${filePath} ];then
        return 2
    fi
    [[ $DDK_HOME = "" ]] && (echo "ERROR: invalid DDK_bin path, please make sure your \$DDK_HOME path is right.";return 2) 
    ret=`${DDK_BIN}/IDE-daemon-client --host ${remote_host}:${remote_port} --hostcmd "wc -l ${filePath}"`
    if [[ $? -ne 0 ]];then
        return 1
    fi

    return 0
}


# ************************uplooad file****************************************
# Description:  upload a file
# $1: local file(absolute)
# $2: remote file path
# ******************************************************************************
function upload_file()
{
    local_file=$1
    remote_path=$2

    file_name=`basename ${local_file}`
    remote_file="${remote_path}/${file_name}"

    #check remote path
    check_remote_file ${remote_file}

    #check whether overwrite remote file
    if [[ $? -eq 0 ]];then
        if [[ ${is_overwrite} == "false" ]];then
            echo "${remote_file} already exists, skip to upload it."
            return 0
        else
            ret=`${DDK_BIN}/IDE-daemon-client --host ${remote_host}:${remote_port} --hostcmd "rm ${remote_file}"`
            if [[ $? -ne 0 ]];then
                echo "ERROR: delete ${remote_host}:${remote_file} failed, please make sure your remote_host ip is right."
                return 1
            fi
        fi
	elif [[ $? -eq 2 ]];then
		return 1
	fi
    	

    ret=`${DDK_BIN}/IDE-daemon-client --host ${remote_host}:${remote_port} --hostcmd "mkdir -p ${remote_path}"`
    if [[ $? -ne 0 ]];then
        echo "ERROR: mkdir ${remote_host}:${remote_path} failed, please make sure your remote_host ip is right."
        return 1
    fi

    #copy to remote path
    ret=`${DDK_BIN}/IDE-daemon-client --host ${remote_host}:${remote_port} --sync ${local_file} ${remote_path}`
    if [[ $? -ne 0 ]];then
        echo "ERROR: sync ${local_file} to ${remote_host}:${remote_path} failed, please make sure your remote_host ip is right."
        return 1
    fi
    return 0
}

# ************************uplooad path****************************************
# Description:  upload a file
# $1: local path(absolute)
# $2: remote path
# $3: ignore_local_path(true/false, default=false)
#    #${local_path}
#    #      |-----path1
#    #              |-----path11
#    #                        |----file1
#    #      |-----path2
#    #              |-----file2
#    #true: upload file1 to ${remote_path}/file1
#    #      upload file2 to ${remote_path}/file2
#    #false/empty: upload file1 upload to ${remote_path}/path1/path11/file1
#    #             upload file2 to ${remote_path}/path2/file2
# ******************************************************************************

function upload_path()
{
    local_path=$1
    remote_supper_path=$2
    ignore_local_path=$3

    file_list=`find ${local_path} -name "*"`
    for file in ${file_list}
    do
        if [[ -d ${file} ]];then
            continue
        fi

        if [[ ${ignore_local_path}"X" == "trueX" ]];then
            remote_file_path=${remote_supper_path}
        else
            remote_file=`echo ${file} | sed "s#${local_path}#${remote_supper_path}#g"`
            remote_file_path=`dirname ${remote_file}`
        fi

        upload_file ${file} ${remote_file_path}
        if [[ $? -ne 0 ]];then
            return 1
        fi
    done
    return 0
}


# ************************parse presenter_altasdk ip****************************
# Description:  parse presenter_altasdk ip right or not
# $1: remote_host ip
# ******************************************************************************

function parse_presenter_altasdk_ip()
{
    valid_ips=""
    remote_host=$1
    for ip_info in `/sbin/ip addr | grep "inet " | awk -F ' ' '{print $2}'`
    do
        ip=`echo ${ip_info} | awk -F '/' '{print $1}'`
        cidr=`echo ${ip_info} | awk -F '/' '{print $2}'`

        valid_ips="${valid_ips}\t${ip}\n"
        mask=`cidr2mask ${cidr}`
        if [[ ${ip}"X" == "X" ]];then
            continue
        fi
        check_ips_in_same_segment ${ip} ${mask} ${remote_host}
        if [[ $? -eq 0 ]];then
            presenter_atlasdk_ip=${ip}
            echo "Find ${presenter_atlasdk_ip} which is in the same segment with ${remote_host}."
            break
        fi
    done

    
    if [[ ${presenter_atlasdk_ip}"X" != "X" ]];then
        return 0
    fi
    
    echo "Can not find ip in the same segment with ${remote_host}."
    while [[ ${presenter_atlasdk_ip}"X" == "X" ]]
    do
        echo -en "Current environment valid ip list:\n${valid_ips}Please choose one which can connect to Atlas DK Developerment Board:"
        read presenter_atlasdk_ip
        if [[ ${presenter_atlasdk_ip}"X" != "X" ]];then
            check_ip_addr ${presenter_atlasdk_ip}
            if [[ $? -ne 0 ]];then
                echo "Invlid ip, please choose again..."
                presenter_atlasdk_ip=""
            else
                #使用grep检测字段，如果没有找到相应的字段，使用$?会返回非零值
                ret=`/sbin/ifconfig | grep ${presenter_atlasdk_ip}`
                if [[ $? -ne 0 ]];then
                    presenter_atlasdk_ip=""
                fi
            fi
        fi
    done
    return 0
}

function parse_presenter_view_ip()
{
    valid_view_ips=""
    for ip_info in `/sbin/ip addr | grep "inet " | awk -F ' ' '{print $2}'`
    do
        ip=`echo ${ip_info} | awk -F '/' '{print $1}'`
        valid_view_ips="${valid_view_ips}\t${ip}\n"
    done

    while [[ ${presenter_view_ip}"X" == "X" ]]
    do
        echo -en "Current environment valid ip list:\n${valid_view_ips}Please choose one to show the presenter in browser(default: 127.0.0.1):"
        read presenter_view_ip
        
        if [[ ${presenter_view_ip}"X" != "X" ]];then
            check_ip_addr ${presenter_view_ip}
            if [[ $? -ne 0 ]];then
                echo "Invlid ip, please choose again..."
                presenter_view_ip=""
            else
                ret=`/sbin/ifconfig | grep ${presenter_view_ip}`
                if [[ $? -ne 0 ]];then
                    echo "Invlid ip, please choose again..."
                    presenter_view_ip=""
                fi
            fi
        else
            presenter_view_ip="127.0.0.1"
        fi
    done
    return 0
}


# ************************check ip in same segment or not****************************************
# Description:  check ip in same segment or not
# $1: checked ip
# $2: compared ip
# $3: compared net mask
# ******************************************************************************
function check_ips_in_same_segment()
{
    ip=$1
    mask=$2
    remote_host=$3

    OLD_IFS_IP="${IFS}"
    IFS="."
    remote_host_attr=(${remote_host})
    ip_attr=(${ip})
    mask_attr=(${mask})
    IFS=${OLD_IFS_IP}
    for i in `seq 0 3`
    do
        ((calc_remote=${remote_host_attr[${i}]}&${mask_attr[${i}]}))
        ((calc_ip=${ip_attr[${i}]}&${mask_attr[${i}]}))

        if [[ calc_remote -ne calc_ip ]];then
            return 1
        fi
    done
    return 0
}


# ************************convert CIDR to netmask****************************************
# Description:  convert CIDR to netmask
# $1: CIDR
# ******************************************************************************
function cidr2mask()
{
   # Number of args to shift, 255..255, first non-255 byte, zeroes
   set -- $(( 5 - ($1 / 8) )) 255 255 255 255 $(( (255 << (8 - ($1 % 8))) & 255 )) 0 0 0
   [ $1 -gt 1 ] && shift $1 || shift
   echo ${1-0}.${2-0}.${3-0}.${4-0}
}

# ************************check ip****************************************
# Description:  check ip valid or not
# $1: ip
# ******************************************************************************

function check_ip_addr()
{
    ip_addr=$1
    echo ${ip_addr} | grep "^[0-9]\{1,3\}\.\([0-9]\{1,3\}\.\)\{2\}[0-9]\{1,3\}$" > /dev/null
    if [ $? -ne 0 ]
    then
        return 1
    fi

    for num in `echo ${ip_addr} | sed "s/./ /g"`
    do
        if [ $num -gt 255 ] || [ $num -lt 0 ]
        then
            return 1
        fi
   done
   return 0
}

