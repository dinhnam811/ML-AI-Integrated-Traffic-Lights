

clear; clc; close all;


videoPath = "video.mp4";   


detector = yolov4ObjectDetector("tiny-yolov4-coco");



v = VideoReader(videoPath);

targetLabels = ["car","truck","bus","police_car","AMBULANCE"]; 

timeList  = [];  
countsPerType = zeros(0, numel(targetLabels)); 


hFig = figure('Name','Car Detection');
hAx  = axes('Parent',hFig);


while hasFrame(v) && ishandle(hFig)
    frame = readFrame(v);
    imshow(frame);
    
    [bboxes,~,labels] = detect(detector, frame);

  
    isTarget = ismember(string(labels), targetLabels);
    
    bboxes   = bboxes(isTarget,:);
    detLabels = labels(isTarget);

   
   counts = zeros(1, numel(targetLabels));
    for i = 1:numel(targetLabels)
        counts(i) = sum(detLabels == targetLabels(i));
    end

    % Annotate detections on frame
    if ~isempty(bboxes)
        frame = insertObjectAnnotation(frame, "rectangle", bboxes, cellstr(detLabels));
    end

    % Show frame
    imshow(frame, 'Parent', hAx);
    title(hAx, sprintf('Time: %.2f s', v.CurrentTime));
    drawnow limitrate;


    timeList(end+1,1) = v.CurrentTime;
    countsPerType(end+1,:) = counts; 
end
T = array2table(countsPerType, 'VariableNames', targetLabels);
T.time_s = timeList; 
T = movevars(T, 'time_s', 'before', 1);  


writetable(T, "vehicle_counts.csv");
disp("Saved vehicle_counts.csv");