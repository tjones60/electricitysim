#!/bin/bash
ray="~/.local/bin/ray"
dir="/opt/electricitysim"
user="ray"
port="6379"
head="localhost"
workers=()

case $1 in

    start)
        ssh $user@$head "$ray start --head --port=$port --node-ip-address=$head"
        for w in "${workers[@]}"
        do
            ssh $user@$w "$ray start --address=$head:$port --node-ip-address=$w"
        done
        ;;

    stop)
        for w in "${workers[@]}"
        do
            ssh $user@$w "$ray stop"
        done
        ssh $user@$head "$ray stop"
        ;;

    exec)
        if [ -z "$2" ]
        then
            echo "Missing job directory: cluster.sh exec <dir>"
        else
            ssh $user@$head "python3 $dir/ray/simulate.py $dir/www/jobs/$2/config.json $dir/www/jobs/$2/output.json $dir/www/jobs/$2/plot.json $ip:$port"
        fi
        ;;

    *)
        echo "Usage: cluster.sh <start|stop|exec>"
        ;;

esac