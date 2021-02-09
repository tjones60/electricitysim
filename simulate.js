function simulate() {
    sendRequest('battery_capacity='+getValue('battery_capacity')+
        '&initial_soc='+getValue('initial_soc')+
        '&max_soc='+getValue('max_soc')+
        '&min_soc='+getValue('min_soc')+
        '&nuclear='+getValue('nuclear')+
        '&solar_scale_factor='+getValue('solar_scale_factor')+
        '&wind_scale_factor='+getValue('wind_scale_factor'), 
        document.getElementById('result'));
}

function getValue(varname) {
    return encodeURIComponent(document.getElementById(varname).value);
}

function sendRequest(args, result=null) {
    console.log(args);
    document.getElementById('progress').innerHTML = 'Processing request...';
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log(this.responseText);
            document.getElementById('progress').innerHTML = 'Done!';
            if (result != null)
                result.innerHTML = this.responseText;
        }
    };
    xhttp.open('POST', 'simulate.php', true);
    xhttp.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    xhttp.send(args);
}

