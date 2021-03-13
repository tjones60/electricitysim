import sys
import configparser
from distutils.util import strtobool
import json
import pandas as pd
import numpy as np
from tabulate import tabulate
# from ray.util.multiprocessing.pool import Pool
import ray
import time

# pool = Pool(ray_address="192.168.100.101:6379")
# config = {}
# data = pd.DataFrame()
# wind_same_as_solar = True
# time_factor = 12
# export_intermediate = False

def import_data(production, curtailment):

    production = pd.read_csv(production,
        names=['date','hour','interval','demand','solar','wind',
        'net_load','renewables','nuclear','large_hydro',
        'imports','generation','thermal','load_less'])

    curtailment = pd.read_csv(curtailment,
        names=['date','hour','interval','wind_curtailment','solar_curtailment'],
        index_col=[0,1,2])

    data = production.join(curtailment,
        on=['date', 'hour', 'interval'],
        how='left')

    data.fillna(0, inplace=True)

    data['wind'] += data['wind_curtailment']
    data['solar'] += data['solar_curtailment']

    #print(tabulate(data.head(20), headers='keys', tablefmt='psql'))

    return data


def import_config(config_file_name):
    global config
    #config = configparser.ConfigParser()
    #config.read(config_file)
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)
    #print(json.dumps(config, indent=4))
    data = import_data(config['data']['production'], config['data']['curtailment'])

    configs = pd.DataFrame(
        columns=['battery','initial_soc','min_soc','max_soc',
        'nuclear','solar','wind'])

    wind_same_as_solar = config['wind']['wind_same_as_solar']
    nuclear_samples = config['nuclear']['nuclear_samples']
    solar_samples = config['solar']['solar_samples']
    battery_samples = config['battery']['battery_samples']

    if wind_same_as_solar:
        wind_samples = 1
    else:
        wind_samples = config['wind']['wind_samples']

    configs['nuclear'] = np.repeat(
        np.linspace(
            config['nuclear']['nuclear_min'],
            config['nuclear']['nuclear_max'],
            nuclear_samples
        ),
        solar_samples * wind_samples * battery_samples
    )

    configs['solar'] = np.tile(
        np.repeat(
            np.linspace(
                config['solar']['solar_min'],
                config['solar']['solar_max'],
                solar_samples
            ),
            wind_samples * battery_samples
        ),
        nuclear_samples
    )

    if wind_same_as_solar:
        configs['wind'] = configs['solar']
    else:
        configs['wind'] = np.tile(
            np.repeat(
                np.linspace(
                    config['wind']['wind_min'],
                    config['wind']['wind_max'],
                    wind_samples
                ),
                battery_samples
            ),
            nuclear_samples * solar_samples
        )

    configs['battery'] = np.tile(
        np.linspace(
            config['battery']['battery_min'],
            config['battery']['battery_max'],
            battery_samples
        ),
        nuclear_samples * solar_samples * wind_samples
    )

    configs['min_soc'] = config['battery']['min_soc']
    configs['max_soc'] = config['battery']['max_soc']
    configs['initial_soc'] = config['battery']['initial_soc']
    configs['wind_same_as_solar'] = config['wind']['wind_same_as_solar']
    configs['export_intermediate'] = config['data']['export_intermediate']
    configs['time_factor'] = config['data']['time_factor']

    # print(tabulate(configs.head(20), headers='keys', tablefmt='psql'))

    config_list = configs.to_dict('records')

    return (config, config_list, data)


@ray.remote
def simulate(config, data):

    output = data.copy()
    
    output['solar'] *= config['solar']
    output['wind'] *= config['wind']
    output['nuclear'] = config['nuclear']
    output['clean'] = output['nuclear'] + output['solar'] + output['wind']
    output['net'] = output['clean'] - output['demand']

    current_value = config['battery'] * config['initial_soc']
    min_value = config['battery'] * config['min_soc']
    max_value = config['battery'] * config['max_soc']

    samples = len(output)
    stored = [0.0] * samples
    battery = [0.0] * samples
    gas = [0.0] * samples
    curtailed = [0.0] * samples
    soc = [0.0] * samples
    net = output['net'].array

    time_factor = config['time_factor']

    for i in range(samples):
        temp = current_value + net[i] / time_factor

        if temp < min_value:
            stored[i] = min_value
            battery[i] = (current_value - min_value) * time_factor
            gas[i] = (min_value - current_value) * time_factor - net[i]
            curtailed[i] = 0.0
        elif temp > max_value:
            stored[i] = max_value
            battery[i] = (current_value - max_value) * time_factor
            gas[i] = 0.0
            curtailed[i] = net[i] - (max_value - current_value) * time_factor
        else:
            stored[i] = current_value + net[i] / time_factor
            battery[i] = -net[i]
            gas[i] = 0.0
            curtailed[i] = 0.0

        if config['battery'] != 0:
            soc[i] = stored[i] / config['battery']
        else:
            soc[i] = 0.0

        current_value = stored[i]

    output['gas'] = pd.Series(gas)
    output['curtailed'] = pd.Series(curtailed)
    output['stored'] = pd.Series(stored)
    output['battery'] = pd.Series(battery)
    output['soc'] = pd.Series(soc)

    total_demand = sum(output['demand']) / time_factor
    total_clean = sum(output['clean']) / time_factor
    total_gas = sum(output['gas']) / time_factor
    total_curtailed = sum(output['curtailed']) / time_factor

    if not config['export_intermediate']:
        output = None

    totals = {
        'clean': (1.0 - total_gas / total_demand) * 100,
        'curtailed': (total_curtailed / total_demand) * 100,
        'demand_value': total_demand,
        'clean_value': total_clean,
        'gas_value': total_gas,
        'curtailed_value': total_curtailed
    }

    # result = {
    #     'config': config,
    #     'output': output,
    #     'totals': totals
    # }

    result_flat = config.copy()
    result_flat.update(totals)

    # print(json.dumps(result_flat))

    return result_flat


def generate_plot_data(config, result_list):

    results = pd.DataFrame(result_list)

    constants = 3
    if config['graph']['x2'] != 'none':
        constants -= 1
    if config['wind']['wind_same_as_solar']:
        constants -= 1
    
    if constants == 1:
        subset = results.groupby(
            results[config['graph']['c1']]
        ).get_group(
            config['graph']['v1']
        )
    elif constants == 2:
        subset = results.groupby(
            [results[config['graph']['c1']],results[config['graph']['c2']]]
        ).get_group(
            (config['graph']['v1'],config['graph']['v2'])
        )
    elif constants == 3:
        subset = results.groupby(
            [results[config['graph']['c1']],results[config['graph']['c2']],results[config['graph']['c3']]]
        ).get_group(
            (config['graph']['v1'],config['graph']['v2'],config['graph']['v3'])
        )

    traces = []
    if config['graph']['x2'] == 'none':
        traces.append({
            'x': subset[config['graph']['x1']].tolist(),
            'y': subset[config['graph']['y']].tolist(),
            'type': 'scatter',
            'name': config['graph']['x1'],
        })
    else:
        for name, group in subset.groupby(config['graph']['x2']):
            traces.append({
                'x': group[config['graph']['x1']].tolist(),
                'y': group[config['graph']['y']].tolist(),
                'type': 'scatter',
                'name': config['graph']['x2'] + " = " + str(name),
            })

    layout = {
        'title': config['graph']['y'] + " vs " + config['graph']['x1'],
        'xaxis': { 'title': config['graph']['x1'] },
        'yaxis': { 'title': config['graph']['y'] }
    }

    plot_data = {
        'traces': traces,
        'layout': layout
    }

    return plot_data


def simulate_distributed(config_list, data):

    data_id = ray.put(data)

    # result_list = []
    # for result_flat in pool.map(simulate, config_list):
    #     result_list.append(result_flat)
    
    result_ids = []
    for config in config_list:
        result_ids.append(simulate.remote(config, data_id))
    
    result_list = []
    for result_flat in ray.get(result_ids):
        result_list.append(result_flat)

    return result_list


if __name__ == '__main__':
    ray.init(address="192.168.100.101:6379")

    print("Generating configs...", end='', flush=True)
    start = time.time()
    config, config_list, data = import_config(sys.argv[1])
    print("Done! ({:.2f}s)".format(time.time()-start))

    print("Running " + str(len(config_list)) + " simuations...", end='', flush=True)
    start = time.time()
    result_list = simulate_distributed(config_list, data)
    print("Done! ({:.2f}s)".format(time.time()-start))

    print("Generating plot data...", end='', flush=True)
    start = time.time()
    plot_data = generate_plot_data(config, result_list)
    print("Done! ({:.2f}s)".format(time.time()-start))

    print("Writing files...", end='', flush=True)
    start = time.time()
    with open(sys.argv[2], 'w') as output_file:
        json.dump(result_list, output_file, indent=4)
    with open(sys.argv[3], 'w') as output_file:
        json.dump(plot_data, output_file, indent=4)
    print("Done! ({:.2f}s)".format(time.time()-start))