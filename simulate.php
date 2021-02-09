<?php

function getValue($varname) {
    if (isset($_POST[$varname])) {
        return $_POST[$varname];
    } else {
        die("$varname not specified");
    }
}

$stamp = date_timestamp_get(date_create());

$i = 0;
while (is_dir("output/$stamp-$i")) {
    $i++;
}
mkdir("output/$stamp-$i");

$config = "[Battery]";
$config .= "\nbattery_capacity = ".getValue("battery_capacity");
$config .= "\ninitial_soc = ".getValue("initial_soc");
$config .= "\nmax_soc = ".getValue("max_soc");
$config .= "\nmin_soc = ".getValue("min_soc");
$config .= "\n\n[Source]";
$config .= "\nnuclear = ".getValue("nuclear");
$config .= "\nsolar_scale_factor = ".getValue("solar_scale_factor");
$config .= "\nwind_scale_factor = ".getValue("wind_scale_factor");
$config .= "\nproduction = data/production-ca-2019.csv";
$config .= "\ncurtailment = data/curtailment-ca-2019.csv";

file_put_contents("output/$stamp-$i/config.ini", $config);

echo shell_exec(escapeshellcmd("python3 simulate.py output/$stamp-$i/config.ini output/$stamp-$i/output.csv"));

?>