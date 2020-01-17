#!/bin/bash
app_name="Head_pose"

stop_pid=`ps -ef | grep "presenter_server\.py" | grep "${app_name}" | awk -F ' ' '{print $2}'`
if [[ ${stop_pid}"X" != "X" ]];then
    echo -e "\033[33mNow do presenter server configuration, kill existing presenter process: kill -9 ${stop_pid}.\033[0m"
    kill -9 ${stop_pid}
fi
echo "presenter sever stop success!"

