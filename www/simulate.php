<?php

if (isset($_POST["config"])) {
    $config = json_decode($_POST["config"]);
} else {
    die("configuration not provided");
}

$lock = fopen("jobs/sim.lock", "w");

if (flock($lock, LOCK_EX)) {

    $stamp = date_timestamp_get(date_create());
    $i = 0;
    while (is_dir("jobs/$stamp-$i"))
        $i++;
    $stamp = "$stamp-$i";
    mkdir("jobs/$stamp");
    file_put_contents("jobs/$stamp/config.json", json_encode($config, JSON_PRETTY_PRINT));
    shell_exec("bash ../ray/cluster.sh exec $stamp");
    echo file_get_contents("jobs/$stamp/plot.json");

    flock($lock, LOCK_UN);

} else {
    echo "Could not obtain lock";
}

fclose($lock);

?>