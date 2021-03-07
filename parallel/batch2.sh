#!/bin/bash
name="renewables-nuclear-4hrbatt"
startx=0
stopx=500
incx=100
starty=0
stopy=10000
incy=2000
rootdir="/opt/electricitysim/parallel"

if [ -d "$rootdir/batch/$name" ]; then
    rm -r batch/$name/*
fi

let x=$startx
while [ $x -le $stopx ]; do

    n="$(echo `printf "%03.0f" $x` | sed 's/..$/.&/')"

    let y=$starty
    while [ $y -le $stopy ]; do

        mkdir -p "$rootdir/batch/$name/$x/$y"

        config="$rootdir/batch/$name/$x/$y/config.ini"

        echo -e "[Battery]" >> $config
        echo -e "battery_capacity = 200000" >> $config
        echo -e "initial_soc = 0.5" >> $config
        echo -e "max_soc = 1.0" >> $config
        echo -e "min_soc = 0.0" >> $config
        echo -e "[Source]" >> $config
        echo -e "nuclear = $y" >> $config
        echo -e "solar_scale_factor = $n" >> $config
        echo -e "wind_scale_factor = $n" >> $config
        echo -e "production = $rootdir/production-ca-2019.csv" >> $config
        echo -e "curtailment = $rootdir/curtailment-ca-2019.csv" >> $config
        
        echo "python3 $rootdir/simulate.py $config $rootdir/batch/$name/$x/$y/output.csv" >> $rootdir/batch/$name/jobs
    
        let y=y+$incy
    done

    let x=x+$incx
done

parallel --slf sshlogin < $rootdir/batch/$name/jobs

output="$rootdir/batch/$name/output.csv"

let x=$startx
while [ $x -le $stopx ]; do

    n="$(echo `printf "%03.0f" $x` | sed 's/..$/.&/')"

    echo -n "$n," >> $output

    let y=$starty
    while [ $y -le $stopy ]; do

        head -n 2 $rootdir/batch/$name/$x/$y/output.csv | sed -n '2p' | tr -d '\n' >> $output
        echo -n "," >> $output

        let y=y+$incy
    done

    echo "" >> $output

    let x=x+$incx
done