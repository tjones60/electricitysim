#!/bin/bash
name="batteries-4xrenewables"
start=0
stop=5000000
inc=50000
rootdir="/mnt/data-volume/calpoly/electricitysim/parallel"

mkdir -p $rootdir/batch/$name
rm -r $rootdir/batch/$name/*

let x=$start
while [ $x -le $stop ]; do

    mkdir "$rootdir/batch/$name/$x"

    #n="$(echo `printf "%03.0f" $x` | sed 's/..$/.&/')"

    echo -e "[Battery]" >> $rootdir/batch/$name/$x/config.ini
    echo -e "battery_capacity = $x" >> $rootdir/batch/$name/$x/config.ini
    echo -e "initial_soc = 0.5" >> $rootdir/batch/$name/$x/config.ini
    echo -e "max_soc = 1.0" >> $rootdir/batch/$name/$x/config.ini
    echo -e "min_soc = 0.0" >> $rootdir/batch/$name/$x/config.ini
    echo -e "[Source]" >> $rootdir/batch/$name/$x/config.ini
    echo -e "nuclear = 0" >> $rootdir/batch/$name/$x/config.ini
    echo -e "solar_scale_factor = 5.0" >> $rootdir/batch/$name/$x/config.ini
    echo -e "wind_scale_factor = 5.0" >> $rootdir/batch/$name/$x/config.ini
    echo -e "production = $rootdir/production-ca-2019.csv" >> $rootdir/batch/$name/$x/config.ini
    echo -e "curtailment = $rootdir/curtailment-ca-2019.csv" >> $rootdir/batch/$name/$x/config.ini

    echo "python3 $rootdir/simulate.py $rootdir/batch/$name/$x/config.ini $rootdir/batch/$name/$x/output.csv" >> $rootdir/batch/$name/jobs

    let x=x+$inc
done

parallel --slf sshlogin < $rootdir/batch/$name/jobs

let x=$start
while [ $x -le $stop ]; do

    #n="$(echo `printf "%03.0f" $x` | sed 's/..$/.&/')"
    echo -n "$x," >> $rootdir/batch/$name/output.csv
    head -n 2 $rootdir/batch/$name/$x/output.csv | sed -n '2p' >> $rootdir/batch/$name/output.csv

    let x=x+$inc
done