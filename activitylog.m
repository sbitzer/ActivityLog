% activitylog(option)
%
% logs activities of the day as input by user
%
% in:
%       option  -   string option, one of:
%                       start,[],not given - start new log for this day
%                       cont, continue     - continue log of this day
% out:
%       a file with name of the form: activitylog_yyyymmdd.mat
% author:
%       Sebastian Bitzer
function activitylog(option)


%% setup
if nargin < 1 || isempty(option)
    option = 'start';
end

fname = sprintf('activitylog_%s.mat',datestr(now,'yyyymmdd'));

jtimes = nan(200,1);
jstr = cell(200,1);

switch option
    case 'start'
        cnt = 1;
        jtimes(cnt) = now;
        jstr{cnt} = 'start log';
        fprintf(1,'Welcome on %s! What are you going to do next?\n(Finish by typing "feierabend")\n',datestr(jtimes(1),'ddd, dd.mm.yyyy'));
    case {'cont','continue'}
        olddata = load(fname);
        if isfield(olddata,'cnt')   % interruption
            cnt = olddata.cnt;
            jtimes(1:cnt) = olddata.jtimes(1:cnt);
            jstr(1:cnt) = olddata.jstr(1:cnt);
        else                        % already typed feierabend
            cnt = length(olddata.jtimes);
            jtimes(1:cnt) = olddata.jtimes(1:cnt);
            jstr(1:cnt) = olddata.jstr(1:cnt);
            jstr{cnt} = 'break';    % replace feierabend with break
        end
        fprintf(1,'Welcome back! You''ll continue from "%s" at %s.\n(Finish by typing "feierabend")\n',jstr{cnt},datestr(jtimes(cnt)));
end


%% logging
while isempty(strfind(lower(jstr{cnt}),'feierabend'))
    cnt = cnt + 1;
    jstr{cnt} = input('Next activity: ','s');
    
    % if delete previous
    if strcmp(jstr{cnt}(1:3),'---')
        % only a delete sign: next input overwrite previous
        if length(jstr{cnt})==3
            cnt = cnt - 2;
            continue
        % current input overwrites previous
        else
            jstr{cnt-1} = jstr{cnt}(4:end);
            cnt = cnt - 1;
        end
    end
    
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

if ~(all(durs>=0))
    warning('There are negative durations!') %#ok<WNTAG>
end

% replace return by corresponding activity
rind = cstrfind(lower(acts),'return');
for r = 1:length(rind)
    acts(rind) = acts(rind-2);
end

% short break indeces, long break indeces
lbreakcls = {'lunch','coffee','golf','physio','cycling'};
sbreakcls = {'break','chat'};
[sbreaki,lbreaki] = findBreaks(acts,sbreakcls,lbreakcls,durs);
worktimes = sum(durs)*ones(1,3);
worktimes(2) = worktimes(2) - sum(durs(lbreaki));
worktimes(3) = worktimes(3) - sum(durs([lbreaki;sbreaki]));

worktimes = worktimes*24;

fprintf(1,'today''s working hours:\n');
disp(worktimes)