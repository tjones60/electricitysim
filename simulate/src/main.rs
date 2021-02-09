use std::collections::HashMap;
use chrono::{NaiveDate, Duration, NaiveDateTime};
use ini::Ini;
use std::fs::File;
use std::io::{BufRead, BufReader};

struct Instant {
    dt: NaiveDateTime,
    demand: f64,
    solar: f64,
    wind: f64,
    nuclear: f64,
    gas: f64,
    clean: f64,
    net: f64,
    battery: f64,
    curtailed: f64,
    stored: f64,
    soc: f64,
}

impl Default for Instant {
    fn default() -> Self {
        Instant {
            dt: NaiveDate::from_ymd(2000, 1, 1).and_hms(0, 0, 0),
            demand: 0.0,
            solar: 0.0,
            wind: 0.0,
            nuclear: 0.0,
            gas: 0.0,
            clean: 0.0,
            net: 0.0,
            battery: 0.0,
            curtailed: 0.0,
            stored: 0.0,
            soc: 0.0,
        }
    }
}

impl Instant {
    fn to_slice(&self) -> [f64; 11] {
        [self.demand,
        self.solar,
        self.wind,
        self.nuclear,
        self.gas,
        self.clean,
        self.net,
        self.battery,
        self.curtailed,
        self.stored,
        self.soc]
    }
}

struct Grid {
    min_soc: f64,
    max_soc: f64,
    initial_soc: f64,
    battery_capacity: f64,

    current_value: f64,
    min_value: f64,
    max_value: f64,
    
    total_demand: f64,
    total_clean: f64,
    total_gas: f64,
    total_curtailed: f64,

    nuclear: f64,
    solar_scale_factor: f64,
    wind_scale_factor: f64,

    data: Vec<Instant>,
    result: [f64; 6],
}

impl Default for Grid {
    fn default() -> Self {
        Grid {
            min_soc: 0.0,
            max_soc: 0.0,
            initial_soc: 0.0,
            battery_capacity: 0.0,
        
            current_value: 0.0,
            min_value: 0.0,
            max_value: 0.0,
            
            total_demand: 0.0,
            total_clean: 0.0,
            total_gas: 0.0,
            total_curtailed: 0.0,
        
            nuclear: 0.0,
            solar_scale_factor: 0.0,
            wind_scale_factor: 0.0,
        
            data: Vec::new(),
            result: [0.0; 6],
        }
    }
}

impl Grid {

    fn new(config_file: &str) -> Self {

        let config = Ini::load_from_file(config_file).unwrap();

        let mut grid = Self {
            min_soc: config.get_from(Some("Battery"), "min_soc").unwrap().parse::<f64>().unwrap(),
            max_soc: config.get_from(Some("Battery"), "max_soc").unwrap().parse::<f64>().unwrap(),
            initial_soc: config.get_from(Some("Battery"), "initial_soc").unwrap().parse::<f64>().unwrap(),
            battery_capacity: config.get_from(Some("Battery"), "battery_capacity").unwrap().parse::<f64>().unwrap(),

            nuclear: config.get_from(Some("Source"), "nuclear").unwrap().parse::<f64>().unwrap(),
            solar_scale_factor: config.get_from(Some("Source"), "solar_scale_factor").unwrap().parse::<f64>().unwrap(),
            wind_scale_factor: config.get_from(Some("Source"), "wind_scale_factor").unwrap().parse::<f64>().unwrap(),

            ..Default::default()
        };

        grid.current_value = grid.battery_capacity * grid.initial_soc;
        grid.min_value = grid.battery_capacity * grid.min_soc;
        grid.max_value = grid.battery_capacity * grid.max_soc;

        grid.import_data(
            config.get_from(Some("Source"), "production").unwrap(),
            config.get_from(Some("Source"), "curtailment").unwrap());

        grid
    }

    fn import_data(&mut self, production_file: &str, curtailment_file: &str) {

        let mut curtailment: HashMap<NaiveDateTime, (f64, f64)> = HashMap::new();
        let file = BufReader::new(File::open(curtailment_file).unwrap());
        for line in file.lines() {
            let line = line.unwrap();
            let vec: Vec<&str> = line.split(',').collect();
            let dt = NaiveDate::parse_from_str(vec.get(0).unwrap(), "%m/%d/%Y").unwrap()
            .and_hms(vec.get(1).unwrap().parse::<u32>().unwrap() - 1, 
            vec.get(2).unwrap().parse::<u32>().unwrap() - 1, 0);
            let wind = match vec.get(3).unwrap().len() {
                0 => 0.0,
                _ => vec.get(3).unwrap().parse::<f64>().unwrap(),
            };
            let solar = match vec.get(4).unwrap().len() {
                0 => 0.0,
                _ => vec.get(4).unwrap().parse::<f64>().unwrap(),
            };
            curtailment.insert(dt, (wind, solar));
        }

        let file = BufReader::new(File::open(production_file).unwrap());
        for line in file.lines() {
            let line = line.unwrap();
            let vec: Vec<&str> = line.split(',').collect();
            let mut inst = Instant {
                dt: NaiveDateTime::parse_from_str(vec.get(0).unwrap(), "%m/%d/%Y %H:%M").unwrap(),
                demand: vec.get(3).unwrap().parse::<f64>().unwrap(),
                solar: vec.get(4).unwrap().parse::<f64>().unwrap(),
                wind: vec.get(5).unwrap().parse::<f64>().unwrap(),
                nuclear: self.nuclear,
                ..Default::default()
            };
            if curtailment.contains_key(&inst.dt) {
                let item = curtailment.get(&inst.dt).unwrap();
                inst.wind += item.0;
                inst.solar += item.1;
            }
            self.data.push(inst);
        }

        
    }

    fn simulate(&mut self) {
        let mut previous: Option<NaiveDateTime> = None;

        for inst in self.data.iter_mut() {
            
            let time_factor = 3600.0 / match previous {
                Some(pdt) => inst.dt.signed_duration_since(pdt).num_seconds(),
                None => Duration::minutes(5).num_seconds(),
            } as f64;
            previous = Some(inst.dt);

            inst.solar *= self.solar_scale_factor;
            inst.wind *= self.wind_scale_factor;
            inst.clean = inst.nuclear + inst.solar + inst.wind;
            inst.net = inst.clean - inst.demand;

            if self.current_value + inst.net / time_factor < self.min_value {
                inst.stored = self.min_value;
                inst.battery = (self.current_value - self.min_value) * time_factor;
                inst.gas = (self.min_value - self.current_value) * time_factor - inst.net;
            } else if self.current_value + inst.net / time_factor > self.max_value {
                inst.stored = self.max_value;
                inst.battery = (self.current_value - self.max_value) * time_factor;
                inst.curtailed = inst.net - (self.max_value - self.current_value) * time_factor;
            } else {
                inst.stored = self.current_value + inst.net / time_factor;
                inst.battery = 0.0 - inst.net;
            }

            self.total_demand += inst.demand / time_factor;
            self.total_clean += inst.clean / time_factor;
            self.total_gas += inst.gas / time_factor;
            self.total_curtailed += inst.curtailed / time_factor;
            inst.soc = match self.battery_capacity == 0.0 {
                true => 0.0,
                false => inst.stored / self.battery_capacity,
            };
            
            self.current_value = inst.stored;
        }
        
        self.result = [(1.0 - self.total_gas / self.total_demand) * 100.0, (self.total_curtailed / self.total_demand) * 100.0,
            self.total_demand, self.total_clean, self.total_gas, self.total_curtailed];
    }

    fn export_data(&self/*, output_file: String*/) {
        //let heading1 = "% Clean,% Curtailed,Total Demand,Total Clean,Total Gas,Total Curtailed";
        //let result_str = self.result.into_iter().map(|x| x.to_string()).collect().join(',');
        
        println!("% Clean: {}<br>\n% Curtailed: {}<br>\nTotal Demand: {}<br>\nTotal Clean: {}<br>\nTotal Gas: {}<br>\nTotal Curtailed: {}<br>\n", 
        &self.result[0], &self.result[1], &self.result[2], &self.result[3], &self.result[4], &self.result[5]);
    }
}

fn main() {
    let mut grid = Grid::new("config.ini");
    grid.simulate();
    grid.export_data();
}