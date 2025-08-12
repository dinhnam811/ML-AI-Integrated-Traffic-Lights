function logTrafficUsingObjects()
   
   A = TrafficLight(0.0);
T = A.redDuration + A.yellowDuration + A.greenDuration;
B = TrafficLight(T - A.redDuration/2);

    time = 0:0.1:2;

  

    fprintf(' Time (s) | Light A  | Light B\n');
    fprintf('-------------------------------\n');

    for t = time
        stateA = A.getState(t);
        stateB = B.getState(t);

        fprintf('  %.1f     | %-7s | %-7s\n', t, stateA, stateB);
    end
end

