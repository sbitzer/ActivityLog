%% load log data
files = dir('activitylog_*.mat');
ndays = length(files);

outfile = fopen('activitylog.csv', 'w');

for d = 1:ndays
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
            fprintf(1, '%s, %s, %s\n', datestr(startt(negind(i)-1)), datestr(endt(negind(i)-1)), acts{negind(i)-1})
            fprintf(1, '%s, %s, %s\n', datestr(startt(negind(i))), datestr(endt(negind(i))), acts{negind(i)})
            fprintf(1, '%s, %s, %s\n', datestr(startt(negind(i)+1)), datestr(endt(negind(i)+1)), acts{negind(i)+1})
            newtstr = input('new time: ', 's');
            usertime = [str2double(newtstr(1:2)),str2double(newtstr(4:5))];
            endt(negind(i)) = day + (usertime(1)*60+usertime(2))/24/60;
            if nact > negind(i)
                startt( negind(i)+1 ) = endt(negind(i));
            end
            fprintf(1, 'new end t: %s\n', datestr(endt(negind(i))))
        end
        durs = endt - startt;
        assert( ~any( durs < 0) )
    end

    for a = 1:nact
        fprintf(outfile, '%.5f, %.5f, %s\n', startt(a), endt(a), acts{a})
    end

end

fclose(outfile)