% Keep all vehicle count columns + add light as last column
recordTrafficLights("vehicle_counts.csv","light_recorder.csv",7,3,8);

% Check the first few rows
head(readtable("light_recorder.csv"))
