function trafficTable = LoadExcelData()
    
    data = readtable('traffic_data.xlsx','VariableNamingRule','preserve');
    trafficTable = data
   
   
end








