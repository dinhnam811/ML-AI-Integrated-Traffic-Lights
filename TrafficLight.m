classdef TrafficLight
    properties
        redDuration = 0.4
        yellowDuration = 0.1
        greenDuration = 0.5
        phaseOffset = 0.0
        tol = 1e-12            % small tolerance for boundary cases
    end

    methods
        function obj = TrafficLight(offset)
            if nargin > 0
                obj.phaseOffset = offset;
            end
        end

        function state = getState(obj, t)
            % Cycle order: Green -> Yellow -> Red (no yellow when Red -> Green)
            totalCycle = obj.redDuration + obj.yellowDuration + obj.greenDuration;

            % Nudge by tol to avoid landing just before boundaries
            tAdjusted = mod(t + obj.phaseOffset + obj.tol, totalCycle);

            gEnd = obj.greenDuration;                    % end of Green
            yEnd = obj.greenDuration + obj.yellowDuration; % end of Yellow

            if tAdjusted < gEnd
                state = "Green";
            elseif tAdjusted < yEnd
                state = "Yellow";   % only appears between Green and Red
            else
                state = "Red";
            end
        end
    end
end
