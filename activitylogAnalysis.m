%% load log data
files = dir('activitylog_*.mat');
ndays = length(files);
if (now-datenum(files(end).name(13:20),'yyyymmdd'))<1   % if last file is
%     ndays = ndays - 1;                                  % from today,
end                                                     % exclude it

nact = 0;
actdaily = struct('times',[],'durs',[],'acts',[]);
for d = 1:ndays
    fdata = load(files(d).name);
    
    actdaily(d).times = fdata.jtimes(2:end-1);
    actdaily(d).durs = diff(fdata.jtimes(2:end));
    actdaily(d).acts = fdata.jstr(2:end-1);
    
    assert(all(actdaily(d).durs>=0))
    
    nact = nact + length(actdaily(d).acts);
    
    % replace return by corresponding activity
    rind = cstrfind(lower(actdaily(d).acts),'return');
    for r = 1:length(rind)
        actdaily(d).acts(rind) = actdaily(d).acts(rind-2);
    end
end


%% daily working times
worktimes = nan(ndays,3);
for d = 1:ndays
    breakind = cstrfind(lower(actdaily(d).acts),{'break','chat'});
    lunchind = cstrfind(lower(actdaily(d).acts),{'lunch','coffee','golf'});
    worktimes(d,:) = sum(actdaily(d).durs);
    worktimes(d,2) = worktimes(d,2) - sum(actdaily(d).durs(lunchind));
    worktimes(d,3) = worktimes(d,3) - sum(actdaily(d).durs([lunchind,breakind]));
end

worktimes = worktimes*24;