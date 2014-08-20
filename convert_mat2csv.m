%% load log data
files = dir('activitylog_*.mat');
ndays = length(files);

nact = 0;
actdaily = struct('times',[],'durs',[],'acts',[],'day',[]);
for d = 741:743
    fdata = load(files(d).name);

    day  = floor(fdata.jtimes(1));
    startt = fdata.jtimes(2:end-1);
    endt = fdata.jtimes(3:end);
    durs = endt - startt;
    acts = fdata.jstr(2:end-1);
    nact = length(acts);

    if any(durs < 0)
        negind = find(durs < 0);
        for i = 1:length(negind)
            disp('Negative duration found! context:')
            fprintf(1, 'activity string: %s\n', acts{negind})
            fprintf(1, 'start t: %s\n', datestr(startt(negind(i))))
            fprintf(1, 'end   t: %s\n', datestr(endt(negind(i))))
            fprintf(1, 'end+1 t: %s\n', datestr(endt(negind(i)+1)))
            newtstr = input('new time: ', 's');
            usertime = regexp(newtstr,'(?<=@)[0-2]\d:[0-5]\d','match');
            usertime = [str2double(usertime{1}(1:2)),str2double(usertime{1}(4:5))];
            endt(negind(i)) = day + (usertime(1)*60+usertime(2))/24/60;
        end
    end

    for a = 1:nact
        fprintf(1, '%s, %s, %s\n', datestr(startt(a)), datestr(endt(a)), acts{a})
    end
    fprintf(1, '\n')

end

