import time
import pandas as pd
import numpy as np
from ray.util.multiprocessing.pool import Pool
pool = Pool()
data = pd.DataFrame()

# import data
def import_data():
    directory = ''

    df_curtail = pd.read_csv('curtailment-ca-2019.csv',
        names=['date','hour','interval','wind_curtailment','solar_curtailment'],
        index_col=[0,1,2])

    # df_curtail.head()
    # print(len(df_curtail))
    # df_curtail.dtypes

    # demand same as load
    df_production = pd.read_csv('production-ca-2019.csv',
        names=['date','hour','interval','demand','solar','wind',
        'net_load','renewables','nuclear','large_hydro',
        'imports','generation','thermal','load_less'])
    df_production['date'] = df_production['date'].str[:10]

    # df_production.head()
    # print(len(df_production))
    # df_production.dtypes

    df_final = df_production.join(df_curtail, on=['date', 'hour', 'interval'], how='left')

    df_final.fillna(0, inplace=True)

    df_final['wind'] += df_final['wind_curtailment']
    df_final['solar'] += df_final['solar_curtailment']

    return df_final

# AGREE ON FILE CONVENTION AND CHANGE TO READ VALUES FROM FILE

def generate_simulation_inputs(file):
    df_configs = pd.DataFrame(columns=["nuclear", "solar_scale_factor", "wind_scale_factor",
                                                                     "min_soc", "max_soc", "initial_soc", 
                                                                     "battery_capacity"])
    
    nuclear_samples = 1
    solar_samples = 1
    wind_samples = 1
    battery_samples = 11

    # df_configs["nuclear"] = np.repeat(np.linspace(1000, 4000, nuclear_samples), 
    #                                   solar_samples*wind_samples*battery_samples)
    # for i in range(0, len(df_configs), 250):
    #   df_configs.loc[i:i+249, 'solar_scale_factor'] = np.repeat(np.linspace(1,2,solar_samples), 
    #                                              wind_samples*battery_samples)
    # for i in range(0, len(df_configs), 50):
    #   df_configs.loc[i:i+49, 'wind_scale_factor'] = np.repeat(np.linspace(1, 2, wind_samples), battery_samples)
    # for i in range(0, len(df_configs), 10):
    #   df_configs.loc[i:i+9, 'battery_capacity'] = np.linspace(1000, 2000, battery_samples)
    # df_configs.head(100)

    df_configs["nuclear"] = np.repeat(np.linspace(2000, 2000, nuclear_samples), 
                                                                        solar_samples*wind_samples*battery_samples)
    solar = np.repeat(np.linspace(4,4,solar_samples), wind_samples*battery_samples)
    solar = list(solar) * (len(df_configs)//len(solar))
    df_configs['solar_scale_factor'] = solar
    wind = np.repeat(np.linspace(4,4,wind_samples), battery_samples)
    wind = list(wind) * (len(df_configs)//len(wind))
    df_configs['wind_scale_factor'] = wind
    battery = np.linspace(0, 500000, battery_samples)
    battery = list(battery) * (len(df_configs)//len(battery))
    df_configs['battery_capacity'] = battery

    if len(df_configs) != len(df_configs.drop_duplicates()):
        raise ValueError

    # implement functionality for changing this later
    df_configs['min_soc'] = 0.0
    df_configs['max_soc'] = 1.0
    df_configs['initial_soc'] = 0.5

    return df_configs

# RUN PYTHON SIMULAITON PROCESS WITH VALUE FROM EACH ROW FOR EACH ROW
# GET OUTPUT; SAVE IN THE DATAFRAME

def simulate(input_dict):
    # might need to import pandas in here; not sure if importing it works across the whole cluster
    # maybe need to make a copy of the dataframe
    export = False
    df_final = data.copy()

    df_final['solar'] *= input_dict['solar_scale_factor']
    df_final['wind'] *= input_dict['wind_scale_factor']
    # could get rid of followig step later
    df_final['nuclear'] = input_dict['nuclear']
    df_final['clean'] = df_final['nuclear'] + df_final['solar'] + df_final['wind']
    df_final['net'] = df_final['clean'] - df_final['demand']

    current_value = input_dict['battery_capacity'] * input_dict['initial_soc']
    min_value = input_dict['battery_capacity'] * input_dict['min_soc']
    max_value = input_dict['battery_capacity'] * input_dict['max_soc']

    # MUST use a loop (or apply function, but that's a loop anyway)
    stored = []
    battery = []
    gas = []
    curtailed = []
    soc = []
    net = df_final['net'].array
    #time_factor = df_final['time_factor'].array
    time_factor = 12 # simulation advances at constant 5 minute intervals

    for i in range(len(df_final)):
        temp = current_value + net[i] / time_factor

        if temp < min_value:
            stored.append(min_value)
            battery.append((current_value - min_value) * time_factor)
            gas.append((min_value - current_value) * time_factor - net[i])
            curtailed.append(0.0)
        elif temp > max_value:
            stored.append(max_value)
            battery.append((current_value - max_value) * time_factor)
            gas.append(0.0)
            curtailed.append(net[i] - (max_value - current_value) * time_factor)
        else:
            stored.append(current_value + net[i] / time_factor)
            battery.append(-net[i])
            gas.append(0.0)
            curtailed.append(0.0)

        if input_dict['battery_capacity'] != 0:
            soc.append(stored[i] / input_dict['battery_capacity'])
        else:
            soc.append(0.0)

        current_value = stored[i]

    df_final['gas'] = pd.Series(gas)
    df_final['curtailed'] = pd.Series(curtailed)
    if export is True:
        df_final['stored'] = pd.Series(stored)
        df_final['battery'] = pd.Series(battery)
        df_final['SOC'] = pd.Series(soc)
        # need to compute path - could just hash string representation of input_dict but need better way
        df_final.to_json(path, orient="index")

    total_demand = sum(df_final['demand']) / time_factor
    total_clean = sum(df_final['clean']) / time_factor
    total_gas = sum(df_final['gas']) / time_factor
    total_curtailed = sum(df_final['curtailed']) / time_factor

    result = {"% Clean":(1.0 - total_gas / total_demand) * 100,
                        "% Curtailed":(total_curtailed / total_demand) * 100,
                        "Total Demand":total_demand,
                        "Total Clean":total_clean,
                        "Total Gas":total_gas,
                        "Total Curtailed":total_curtailed}

    # maybe need garbage collection command
    print((input_dict, result))
    return (input_dict, result)
    
def simulate_distributed(configs):
    start = time.time()
    
    results = []
    config_list = configs.to_dict('records')
    for result in pool.map(simulate, config_list):
            results.append(result)
            
    print("Finished in: {:.2f}s".format(time.time()-start))


if __name__ == "__main__":
        data = import_data()
        configs = generate_simulation_inputs("")
        simulate_distributed(configs)