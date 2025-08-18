function recordTrafficLights(inCsv, outCsv, nGreen, nYellow, nRed)
% recordTrafficLightsWithPreempt
% Reads vehicle_counts CSV, creates repeating light states by row counts,
% then applies ambulance preemption
% If AMBULANCE >= 1 on any row -> light becomes "Green" for that row.
% Writes all original columns + final 'light' column to outCsv.
% Usage: recordTrafficLightsWithPreempt("vehicle_counts.csv","light_recorder.csv",7,3,8)

    if nargin < 5
        error("Usage: recordTrafficLights(inCsv,outCsv,nGreen,nYellow,nRed)");
    end

    % Load input
    T = readtable(inCsv);
    vars = string(T.Properties.VariableNames);
    assert(ismember("time_s", vars), "Input CSV must contain 'time_s'.");
    assert(ismember("AMBULANCE", vars), "Input CSV must contain 'AMBULANCE' (case-sensitive).");

    t = T.time_s(:);
    assert(numel(t) >= 2, "Need at least two timestamps.");

    % Derive dt and durations from desired row counts
    dt = median(diff(t));
    tG = nGreen  * dt;
    tY = nYellow * dt;
    tR = nRed    * dt;
    cycle = tG + tY + tR;

    % Align cycle start to first timestamp for exact row counts
    t0   = t(1);
    tmod = mod(t - t0, cycle);

    % Base light pattern by row counts
    light = strings(numel(t),1);
    light(tmod < tG)                 = "Green";
    light(tmod >= tG & tmod < tG+tY) = "Yellow";
    light(tmod >= tG+tY)             = "Red";

    % Ambulance preemption (per-row override) 
    amb = T.AMBULANCE(:);          
    maskAmb = amb >= 1;
    light(maskAmb) = "Green";

    % Append 'light' as the last column and save 
    T.light = light;
    writetable(T, outCsv);

    fprintf("Recorded %d rows into %s (dt≈%.6fs, cycle≈%.6fs)\n", height(T), outCsv, dt, cycle);
end
