<?php

function getValue($varname) {
    if (isset($_POST[$varname])) {
        return $_POST[$varname];
    } else {
        die("$varname not specified");
    }
}

echo file_get_contents(getValue("fname"));

?>