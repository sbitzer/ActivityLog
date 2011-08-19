function [sbreaki,lbreaki] = findBreaks(acts,sbreakcls,lbreakcls,durs,longtime)

if nargin < 5
    longtime = 10;
end

%% find indeces based on classes
sbreaki = cstrfind(lower(acts),sbreakcls);
lbreaki = cstrfind(lower(acts),lbreakcls);

sbreaki = sbreaki(:);
lbreaki = lbreaki(:);


%% check whether small break class also contains big breaks by duration
long = durs(sbreaki) > longtime/24/60;     % duration more than 10 minutes
lbreaki = [lbreaki; sbreaki(long)];
sbreaki = sbreaki(~long);
