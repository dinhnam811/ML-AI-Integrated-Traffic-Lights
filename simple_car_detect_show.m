clear; clc; close all;

% Import the input video
videoPath = "traf.mov";   

% Initialize YOLOv4 object detector with a small pre-trained model
detector = yolov4ObjectDetector("tiny-yolov4-coco");


v = VideoReader(videoPath);

% Define the target classes to detect
targetLabels = ["car","truck","bus","police_car","AMBULANCE"]; 

timeList  = [];  
countsPerType = zeros(0, numel(targetLabels)); 

% Set up display window for visualization
hFig = figure('Name','Car Detection');
hAx  = axes('Parent',hFig);

% Loop through each frame of the video
while hasFrame(v) && ishandle(hFig)
    
    frame = readFrame(v);
    imshow(frame);
    
    % Detect objects in the frame
    [bboxes,~,labels] = detect(detector, frame);

    % Keep only the detections that match our target labels
    isTarget = ismember(string(labels), targetLabels);
    bboxes   = bboxes(isTarget,:);
    detLabels = labels(isTarget);

    % Count occurrences of each target label
    counts = zeros(1, numel(targetLabels));
    for i = 1:numel(targetLabels)
        counts(i) = sum(detLabels == targetLabels(i));
    end

    % Annotate detections on the frame (bounding boxes + labels)
    if ~isempty(bboxes)
        frame = insertObjectAnnotation(frame, "rectangle", bboxes, cellstr(detLabels));
    end

    % Display the annotated frame
    imshow(frame, 'Parent', hAx);
    title(hAx, sprintf('Time: %.2f s', v.CurrentTime));  % show video time
    drawnow limitrate;  % update graphics efficiently

    
    timeList(end+1,1) = v.CurrentTime;
    countsPerType(end+1,:) = counts; 
end

% Convert results into a table with column names
T = array2table(countsPerType, 'VariableNames', targetLabels);


T.time_s = timeList;
T = movevars(T, 'time_s', 'before', 1);  

% Save the results to CSV
writetable(T, "vehicle_counts.csv");
disp("Saved vehicle_counts.csv");
