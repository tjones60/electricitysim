import sys
import datetime
import time
import os
import re
import csv
import configparser
import urllib.request

class Instant:

    def __init__(self):
        self.demand = 0.0
        self.solar = 0.0
        self.wind = 0.0
        self.nuclear = 0.0
        self.gas = 0.0
        self.clean = 0.0
        self.net = 0.0
        self.battery = 0.0
        self.curtailed = 0.0
        self.stored = 0.0
        self.soc = 0.0

    def to_array(self):
        return [self.demand,\
            self.solar,\
            self.wind,\
            self.nuclear,\
            self.gas,\
            self.clean,\
            self.net,\
            self.battery,\
            self.curtailed,\
            self.stored,\
            self.soc]

    def __repr__(self):
        return str(self.to_array())

class Grid:

    def __init__(self, config_file):
        
        self.min_soc = 0.0
        self.max_soc = 0.0
        self.initial_soc = 0.0
        self.battery_capacity = 0.0

        self.current_value = 0.0
        self.min_value = 0.0
        self.max_value = 0.0
        
        self.total_demand = 0.0
        self.total_clean = 0.0
        self.total_gas = 0.0
        self.total_curtailed = 0.0

        self.nuclear = 0.0
        self.solar_scale_factor = 0.0
        self.wind_scale_factor = 0.0

        self.data = {}
        self.result = []

        self.config = configparser.ConfigParser()
        self.import_config(config_file)
        
    def import_config(self, config_file):
        self.config.read(config_file)
        self.min_soc = float(self.config["Battery"]["min_soc"])
        self.max_soc = float(self.config["Battery"]["max_soc"])
        self.battery_capacity = float(self.config["Battery"]["battery_capacity"])
        self.initial_soc = float(self.config["Battery"]["initial_soc"])
        self.nuclear = float(self.config["Source"]["nuclear"])
        self.solar_scale_factor = float(self.config["Source"]["solar_scale_factor"])
        self.wind_scale_factor = float(self.config["Source"]["wind_scale_factor"])
        self.import_data(self.config["Source"]["production"], self.config["Source"]["curtailment"])

    def import_data(self, production, curtailment):

        with open(production, "r", encoding="utf-8-sig") as f:
            contents = f.readlines()
            for item in contents:
                arr = item.strip().split(",")
                dt = datetime.datetime.strptime(arr[0].strip(), "%m/%d/%Y %H:%M")
                inst = Instant()
                inst.demand = float(arr[3])
                inst.solar = float(arr[4])
                inst.wind = float(arr[5])
                inst.nuclear = self.nuclear
                self.data[dt] = inst

        with open(curtailment, "r", encoding="utf-8-sig") as f:
            contents = f.readlines()
            for item in contents:
                arr = item.strip().split(",")
                dt = datetime.datetime.strptime(arr[0], "%m/%d/%Y")
                dt = dt.replace(hour=(int(arr[1]) - 1), minute=(int(arr[2]) * 5 - 5))
                if dt in self.data:
                    if len(arr[3]) > 0:
                        self.data[dt].wind += float(arr[3])
                    if len(arr[4]) > 0:
                        self.data[dt].solar += float(arr[4])

        self.current_value = self.battery_capacity * self.initial_soc
        self.min_value = self.battery_capacity * self.min_soc
        self.max_value = self.battery_capacity * self.max_soc

    def simulate(self):
        previous = None
        delta = datetime.timedelta(minutes=5)

        for dt in sorted(self.data):
            
            if previous is not None:
                delta = dt - previous
            time_factor = 3600.0 / delta.seconds
            previous = dt

            inst = self.data[dt]
            inst.solar *= self.solar_scale_factor
            inst.wind *= self.wind_scale_factor
            inst.clean = inst.nuclear + inst.solar + inst.wind
            inst.net = inst.clean - inst.demand

            if self.current_value + inst.net / time_factor < self.min_value:
                inst.stored = self.min_value
                inst.battery = (self.current_value - self.min_value) * time_factor
                inst.gas = (self.min_value - self.current_value) * time_factor - inst.net
            elif self.current_value + inst.net / time_factor > self.max_value:
                inst.stored = self.max_value
                inst.battery = (self.current_value - self.max_value) * time_factor
                inst.curtailed = inst.net - (self.max_value - self.current_value) * time_factor
            else:
                inst.stored = self.current_value + inst.net / time_factor
                inst.battery = 0.0 - inst.net

            self.total_demand += inst.demand / time_factor
            self.total_clean += inst.clean / time_factor
            self.total_gas += inst.gas / time_factor
            self.total_curtailed += inst.curtailed / time_factor
            inst.soc = 0.0 if self.battery_capacity == 0.0 else inst.stored / self.battery_capacity
            
            self.current_value = inst.stored
        
        self.result = [(1.0 - self.total_gas / self.total_demand) * 100, (self.total_curtailed / self.total_demand) * 100,\
            self.total_demand, self.total_clean, self.total_gas, self.total_curtailed]
        print("% Clean % Curtailed Total Demand Total Clean Total Gas Total Curtailed<br>")
        print(["{:.2f}".format(x) for x in self.result])

    def export_data(self, fname):
        output = [["% Clean","% Curtailed","Total Demand","Total Clean","Total Gas","Total Curtailed"],\
            ["{:.2f}".format(x) for x in self.result],\
            ["Date/Time","Demand","Solar","Wind","Nuclear","Gas","Clean","Net","Battery","Curtailed","Stored","SOC"]]
        for dt in sorted(self.data):
            output.append([dt.strftime("%Y-%m-%d %H:%M")] + ["{:.2f}".format(x) for x in self.data[dt].to_array()])

        with open(fname, "w") as f:
            writer = csv.writer(f,delimiter=',',lineterminator='\n')
            writer.writerows(output)

if __name__ == "__main__":
    g = Grid(sys.argv[1])
    g.simulate()
    g.export_data(sys.argv[2])