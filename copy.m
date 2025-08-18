v = VideoReader(videoPath);


timeList  = [];  
countList = [];  


hFig = figure('Name','Car Detection');
hAx  = axes('Parent',hFig);


while hasFrame(v) && ishandle(hFig)
    frame = readFrame(v);
    [bboxes,~,labels] = detect(detector, frame);

  
    isCar  = strcmp(string(labels), "car");
    
    bboxes = bboxes(isCar,:);
    numCars = size(bboxes,1);

   
    if numCars > 0
        tags = "Car #" + string(1:numCars).';
        frame = insertObjectAnnotation(frame, "rectangle", bboxes, cellstr(tags));
    end


    imshow(frame, 'Parent', hAx);
    title(hAx, sprintf('Time: %.2f s | Cars: %d', v.CurrentTime, numCars));
    drawnow limitrate;


    timeList(end+1,1)  = v.CurrentTime;
    countList(end+1,1) = numCars;       
end

T = table(timeList, countList, 'VariableNames', {'time_s','car_count'});
writetable(T, "car_counts.csv");
disp("Saved car_counts.csv");
