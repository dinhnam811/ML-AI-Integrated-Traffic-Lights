frame0 = readFrame(vr);  % first frame
figure; imshow(frame0); title("Draw lane ROIs (double-click to finish each)");
hold on;

lanePolys = {};
answer = 'y';
i = 1;
while lower(answer) == 'y'
    p = drawpolygon('Color','y');   %#ok<DRAWPO>  (interactive)
    lanePolys{i} = p.Position;      % Nx2 [x,y]
    answer = questdlg('Add another lane ROI?','ROIs','Yes','No','No');
    if strcmpi(answer,'Yes'), answer='y'; else, answer='n'; end
    i = i+1;
end

% Counting lines (one per lane)
countLines = cell(numel(lanePolys),1);
for i = 1:numel(lanePolys)
    title(sprintf('Draw counting line for Lane %d',i));
    l = drawline('Color','c');      %#ok<DRAWPO>
    countLines{i} = l.Position;     % 2x2 [x1 y1; x2 y2]
end

save roi_config.mat lanePolys countLines
close all
vr.CurrentTime = 0; % rewind
