%% load log data
files = dir('oldlogs/activitylog_*.mat');
ndays = length(files);

outfile = fopen('activitylog_tmp.csv', 'w');

onesecond = 1 / 24 / 60 / 60;

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

    if floor(startt(1)) == 734724
        durs
    end

    % because in the sqlite database I have a resolution of 1 second;
    % use 1.5 seconds to avoid problems with the discretisation
    smallind = find(durs < 1.5*onesecond);
    for ind = smallind
        if ~isempty(ind)
            warning('updating %13.6f to %13.6f', endt(ind), startt(ind) + 1.5*onesecond)
            endt(ind) = startt(ind) + 1.5*onesecond;
            startt(ind+1) = endt(ind);
        end
    end

    for a = 1:nact
        if strncmp(acts{a}, 'return', 6)
            acts{a} = acts{a-2};
        end

        % replace some old job strings which do not conform to later syntax
        if strncmp(acts{a}, 'coding', 6) && length(acts{a}) > 6 && ...
            ~strncmp(acts{a}(7:end), ' for', 4)
            acts{a} = ['coding for', acts{a}(7:end)];
        end
        if strncmp(acts{a}, 'programming', 11) && length(acts{a}) > 11 && ...
            ~strncmp(acts{a}(12:end), ' for', 4)
            acts{a} = ['programming for', acts{a}(12:end)];
        end
        if strncmp(acts{a}, 'managing', 8) && length(acts{a}) > 8 && ...
            ~strncmp(acts{a}(9:end), ' for', 4)
            acts{a} = ['admin for', acts{a}(9:end)];
        end
        if strncmp(acts{a}, 'documenting', 11) && length(acts{a}) > 11 && ...
            ~strncmp(acts{a}(12:end), ' for', 4)
            acts{a} = ['documenting for', acts{a}(12:end)];
        end
        if strncmp(acts{a}, 'writing email', 13)
            acts{a} = ['email', acts{a}(14:end)];
        end
        if strncmp(acts{a}, 'writing review', 14)
            acts{a} = ['review', acts{a}(15:end)];
        end
        if strncmp(acts{a}, 'writing', 7) && length(acts{a}) > 7 && ...
            ~strncmp(acts{a}(8:end), ' for', 4)
            acts{a} = ['writing for', acts{a}(8:end)];
        end
        if strncmp(acts{a}, 'preparing', 9) && ...
            isempty(strfind(acts{a}, 'for')) && ...
            isempty(strfind(acts{a}, 'with'))

            acts{a} = ['preparing talk for', acts{a}(10:end)];
        end
        if strncmp(acts{a}, 'preparing lecture for teaching', 30)
            acts{a} = ['preparing talk for teaching', acts{a}(31:end)];
        end
        if strncmp(acts{a}, 'groupmeeting and', 16)
            acts{a} = 'groupmeeting';
        end

        fprintf(outfile, '%.6f; %.6f; %s\n', startt(a), endt(a), acts{a})
    end

end

fclose(outfile)