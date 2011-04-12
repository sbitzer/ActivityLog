%% activity log
%  logs activities of the day
jtimes = nan(200,1);
jstr = cell(200,1);

jtimes(1) = now;
jstr{1} = 'start log';

fname = sprintf('activitylog_%s.mat',datestr(jtimes(1),'yyyymmdd'));

fprintf(1,'Welcome on %s! What are you going to do next?\n(Finish by typing "feierabend")\n',datestr(jtimes(1),'ddd, dd.mm.yyyy'));

cnt = 1;
while isempty(strfind(lower(jstr{cnt}),'feierabend'))
    cnt = cnt + 1;
    jstr{cnt} = input('Next activity: ','s');
    
    % allow that user gives time in format: @HH:MM
    usertime = regexp(jstr{cnt},'(?<=@)[0-2]\d:[0-5]\d','match');
    if isempty(usertime)
        jtimes(cnt) = now;
    else
        usertime = [str2double(usertime{1}(1:2)),str2double(usertime{1}(4:5))];
        jtimes(cnt) = floor(now) + (usertime(1)*60+usertime(2))/24/60;
    end
    
    save(fname)
end

jstr = jstr(1:cnt);
jtimes = jtimes(1:cnt);

save(fname,'jstr','jtimes')


%% working time for this day
durs = diff(jtimes(2:end));
acts = jstr(2:end-1);

if (all(durs>=0))
    warning('There are negative durations!')
end

% replace return by corresponding activity
rind = cstrfind(lower(acts),'return');
for r = 1:length(rind)
    acts(rind) = acts(rind-2);
end

breakind = cstrfind(lower(acts),{'break','chat'});
lunchind = cstrfind(lower(acts),{'lunch','coffee'});
worktimes = sum(durs)*ones(1,3);
worktimes(2) = worktimes(2) - sum(durs(lunchind));
worktimes(3) = worktimes(3) - sum(durs([lunchind,breakind]));

worktimes = worktimes*24;

fprintf(1,'today''s working hours:\n');
disp(worktimes)