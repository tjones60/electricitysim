var buffer;
var data;

function simulate() {
    sendRequest('simulate.php',
        'battery_capacity='+getValue('battery_capacity')+
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

function sendRequest(script, args=null, result=null, callback=null) {
    console.log(args);
    document.getElementById('progress').innerHTML = 'Processing request...';
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log(this.responseText);
            document.getElementById('progress').innerHTML = 'Done!';
            if (result != null)
                result.innerHTML = this.responseText;
            if (callback != null)
                callback(this.responseText);
        }
    };
    xhttp.open('POST', script, true);
    xhttp.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    xhttp.send(args);
}

function comparefloatstring(a, b) {
    return parseFloat(a) - parseFloat(b);
}

function getoutput() {
    sendRequest("getfile.php", "fname=renewables-nuclear-4hrbatt-reduced.csv", null, parseoutput);
}

function parseoutput(outputstr) {
    data = {};
    lines = outputstr.split("\r\n");
    for (var i = 0; i < lines.length; i++) {
        var values = lines[i].split(",");
        x = parseFloat(values[0]);
        data[x] = {};
        for (var j = 1; j <= 21; j += 2) {
            var y = (j-1)*1000;
            data[x][y] = {}
            data[x][y]["clean"] = values[j];
            data[x][y]["curtailed"] = values[j+1];
        }
    }

    var keys = Object.keys(data).sort(comparefloatstring);
    var values = {};
    for (var i = 0; i < keys.length; i++) {
        var keys2 = Object.keys(data[keys[i]]).sort(comparefloatstring);
        for (var j = 0; j < keys2.length; j++) {
            if (!(keys2[j] in values)) {
                values[keys2[j]] = [];
            }
            values[keys2[j]].push(data[keys[i]][keys2[j]]["clean"]);
        }
    }

    var names = Object.keys(values).sort(comparefloatstring);
    var traces = [];
    for (var i = 0; i < names.length; i++) {
        traces.push({
            x: keys,
            y: values[names[i]],
            type: 'scatter',
            name: names[i],
        });
    }

    var layout = {
        title: 'Effect of Increasing Renewables',
        xaxis: {
            title: 'Renewables Scale Factor',
        },
        yaxis: {
            title: 'Percent Clean Energy',
        }
    };

    Plotly.newPlot(document.getElementById('plot'), traces, layout);
}