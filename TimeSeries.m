
TrafficData = LoadExcelData();

time = TrafficData{:,1};
values = TrafficData{:,2:end};   

traffic_ts = timeseries(values, time);  

whos traffic_ts




