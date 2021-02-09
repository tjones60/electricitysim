#!/bin/bash
name="batteries-4xrenewables"
start=0
stop=5000000
inc=50000

mkdir -p batch/$name
rm -r batch/$name/*

let x=$start
while [ $x -le $stop ]; do

    mkdir "batch/$name/$x"

    #n="$(echo `printf "%03.0f" $x` | sed 's/..$/.&/')"

    echo -e "[Battery]" >> batch/$name/$x/config.ini
    echo -e "battery_capacity = $x" >> batch/$name/$x/config.ini
    echo -e "initial_soc = 0.5" >> batch/$name/$x/config.ini
    echo -e "max_soc = 1.0" >> batch/$name/$x/config.ini
    echo -e "min_soc = 0.0" >> batch/$name/$x/config.ini
    echo -e "[Source]" >> batch/$name/$x/config.ini
    echo -e "nuclear = 0" >> batch/$name/$x/config.ini
    echo -e "solar_scale_factor = 5.0" >> batch/$name/$x/config.ini
    echo -e "wind_scale_factor = 5.0" >> batch/$name/$x/config.ini
    echo -e "production = data/production-ca-2019.csv" >> batch/$name/$x/config.ini
    echo -e "curtailment = data/curtailment-ca-2019.csv" >> batch/$name/$x/config.ini

    echo "python3 simulate.py batch/$name/$x/config.ini batch/$name/$x/output.csv" >> batch/$name/jobs

    let x=x+$inc
done

parallel --jobs 6 < batch/$name/jobs

let x=$start
while [ $x -le $stop ]; do

    #n="$(echo `printf "%03.0f" $x` | sed 's/..$/.&/')"
    echo -n "$x," >> batch/$name/output.csv
    head -n 2 batch/$name/$x/output.csv | sed -n '2p' >> batch/$name/output.csv

    let x=x+$inc
done