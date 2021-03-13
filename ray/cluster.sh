#!/bin/bash
ray="~/.local/bin/ray"
user="ray"
port="6379"
head="192.168.100.101"
workers=( "192.168.100.102" "192.168.100.103" "192.168.100.104" )

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

    *)
        echo "Usage: cluster.sh <start|stop>"
        ;;

esac