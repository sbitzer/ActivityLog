%% load log data
files = dir('oldlogs/activitylog_*.mat');
ndays = length(files);

outfile = fopen('activitylog_tmp.csv', 'w');

for d = 1:ndays
    fdata = load(fullfile('oldlogs', files(d).name));

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
            newtstr = input('new time (- for start, + for end, e.g., -14:43): ', 's');
            usertime = [str2double(newtstr(2:3)),str2double(newtstr(5:6))];

            % change start time
            if strcmp(newtstr(1), '-')
                startt(negind(i)) = day + (usertime(1)*60+usertime(2))/24/60;
                if negind(i) > 1
                    endt( negind(i)-1 ) = startt(negind(i));
                end
                fprintf(1, 'new start t: %s\n', datestr(startt(negind(i))))
            % change end time
            else
                endt(negind(i)) = day + (usertime(1)*60+usertime(2))/24/60;
                if nact > negind(i)
                    startt( negind(i)+1 ) = endt(negind(i));
                end
                fprintf(1, 'new end t: %s\n', datestr(endt(negind(i))))
            end
        end
        durs = endt - startt;
        assert( ~any( durs < 0) )
    end

    for a = 1:nact
        fprintf(outfile, '%.5f; %.5f; %s\n', startt(a), endt(a), acts{a})
    end

end

fclose(outfile)