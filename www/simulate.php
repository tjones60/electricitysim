<?php

$dir = "/opt/electricitysim";
$user = "ray";
$ip = "192.168.2.231";

if (isset($_POST["config"])) {
    $config = json_decode($_POST["config"]);
} else {
    die("$varname not specified");
}

$stamp = date_timestamp_get(date_create());
mkdir("jobs/$stamp");

file_put_contents("$dir/www/jobs/$stamp/config.json", json_encode($config, JSON_PRETTY_PRINT));

$cmd  = "ssh $user@$ip '~/.local/bin/ray exec $dir/ray/cluster.yaml ";
$cmd .= "\"python3 $dir/ray/simulate.py $dir/www/jobs/$stamp/config.json $dir/www/jobs/$stamp/output.json $dir/www/jobs/$stamp/plot.json\"'";

shell_exec($cmd);

echo file_get_contents("$dir/www/jobs/$stamp/plot.json");

?>