var buffer;
var data;

function getValue(varname) {
    return document.getElementById(varname).value;
}

function getChecked(varname) {
    return document.getElementById(varname).checked;
}

function simulate() {

    var config = {
        "nuclear": {
            "nuclear_min": parseFloat(getValue('nuclear_min')),
            "nuclear_max": parseFloat(getValue('nuclear_max')),
            "nuclear_samples": parseInt(getValue('nuclear_samples'))
        },
        "solar": {
            "solar_min": parseFloat(getValue('solar_min')),
            "solar_max": parseFloat(getValue('solar_max')),
            "solar_samples": parseInt(getValue('solar_samples'))
        },
        "wind": {
            "wind_min": parseFloat(getValue('wind_min')),
            "wind_max": parseFloat(getValue('wind_max')),
            "wind_samples": parseInt(getValue('wind_samples')),
            "wind_same_as_solar": getChecked('wind_same_as_solar')
        },
        "battery": {
            "battery_min": parseFloat(getValue('battery_min')),
            "battery_max": parseFloat(getValue('battery_max')),
            "battery_samples": parseInt(getValue('battery_samples')),
            "initial_soc": parseFloat(getValue('initial_soc')),
            "max_soc": parseFloat(getValue('max_soc')),
            "min_soc": parseFloat(getValue('min_soc'))
        },
        "data": {
            "production": getValue("production"),
            "curtailment": getValue("curtailment"),
            "time_factor": parseFloat(getValue('time_factor')),
            "export_intermediate": getChecked('export_intermediate')
        },
        "graph": {
            "x1": getValue("x1"),
            "x2": getValue("x2"),
            "c1": getValue('c1'),
            "v1": parseFloat(getValue('v1')),
            "c2": getValue('c2'),
            "v2": parseFloat(getValue('v2')),
            "c3": getValue('c3'),
            "v3": parseFloat(getValue('v3')),
            "y": getValue('y'),
        }
    };

    console.log(JSON.stringify(config, null, 4));

    sendRequest('simulate.php',
        'config='+encodeURIComponent(JSON.stringify(config)), 
        null, draw);
}

function draw(data_str) {
    var data = JSON.parse(data_str);
    Plotly.newPlot(document.getElementById('plot'), data.traces, data.layout);
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