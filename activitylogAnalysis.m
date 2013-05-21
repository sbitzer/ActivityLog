%% definition of classes of activities
acls.bgbreak  = {'lunch','coffee','golf','physio','cycling'};       % large break
acls.smbreak  = {'break','chat'};                         % small break
acls.instmeet = {'imaging meeting','institute colloquium','neurotk','workshop','guest lecture', 'guest talk'}; % institute-wide meetings
acls.grmeet   = {'groupmeeting','labmeeting','dysco'};     % group meetings
acls.indmeet  = {'meeting with'};                         % meetings with individual persons
acls.talk     = {'presenting'};
acls.litsrch  = {'literature search','scanning new articles'};
acls.coding   = {'coding','programming'};
acls.maths    = {'deriving'};
acls.exp      = {'experiments','experimenting'};
acls.admin    = {'admin','email'};
acls.figure   = {'making figure'};
acls.reading  = {'reading'};
acls.watch    = {'watching'};
acls.review   = {'review'};
acls.prep     = {'preparing'};
acls.poster   = {'making poster'};
acls.video    = {'making video'};
acls.manage   = {'managing'};
acls.thinking = {'thinking'};
acls.doc      = {'documenting'};
acls.writing  = {'writing','notes'};
acls.learn    = {'attending lecture', 'lecture'};
acls.social   = {'social meeting', 'meeting with everyone'};

aclsnames = fieldnames(acls);
nacls = length(aclsnames);


%% load log data
files = dir('activitylog_*.mat');
ndays = length(files);
if (now-datenum(files(end).name(13:20),'yyyymmdd'))<1   % if last file is
    ndays = ndays - 1;                                  % from today,
end                                                     % exclude it

nact = 0;
actdaily = struct('times',[],'durs',[],'acts',[],'day',[]);
for d = 1:ndays
    fdata = load(files(d).name);
    
    actdaily(d).times = fdata.jtimes(2:end-1);
    actdaily(d).durs = diff(fdata.jtimes(2:end));
    actdaily(d).acts = fdata.jstr(2:end-1);
    actdaily(d).day  = floor(fdata.jtimes(1));
    
    % if there are negative durations
    if any(actdaily(d).durs < 0)
        % throw error naming the day
        error('negative durations in activitylog_%s.mat', datestr(actdaily(d).day, 'yyyymmdd'))
    end
    
    nact = nact + length(actdaily(d).acts);
    
    % replace return by corresponding activity
    rind = cstrfind(lower(actdaily(d).acts),'return');
    for r = 1:length(rind)
        actdaily(d).acts(rind) = actdaily(d).acts(rind-2);
    end
    
    % replace undescriptive "paper" with "rrnn paper" when occuring in
    % certain time interval
    if actdaily(d).day < datenum(2011,08,01)
        % also replace "project paper", but not "groupmeeting paper"
        actdaily(d).acts = regexprep(actdaily(d).acts,...
            '(project paper)|((?<!groupmeeting )paper)','rrnn paper');
    end
end

actdays = cell(1,ndays);
[actdays{:}] = actdaily.day;
actdays = cell2mat(actdays);

actall.acts = cell(nact,1);
actall.durs = nan(nact,1);
actall.times = nan(nact,1);
cnt = 0;
for d = 1:ndays
    na = size(actdaily(d).durs,1);
    actall.acts(cnt+(1:na)) = lower(actdaily(d).acts);
    actall.durs(cnt+(1:na)) = actdaily(d).durs;
    actall.times(cnt+(1:na)) = actdaily(d).times;
    cnt = cnt + na;
end


%% check whether all activities are associated with at least one class
inds = [];
for c = 1:nacls
    inds = [inds,cstrfind(actall.acts,acls.(aclsnames{c}))]; %#ok<AGROW>
end
inds = unique(inds);
if length(inds)<nact
    actall.acts(setdiff(1:nact,inds))
else
    disp('All activities covered!')
end


%% daily working times
worktimes = nan(ndays,3);
for d = 1:ndays
    [sbreaki,lbreaki] = findBreaks(actdaily(d).acts,acls.smbreak,acls.bgbreak,actdaily(d).durs);
    worktimes(d,:) = sum(actdaily(d).durs);
    worktimes(d,2) = worktimes(d,2) - sum(actdaily(d).durs(lbreaki));
    worktimes(d,3) = worktimes(d,3) - sum(actdaily(d).durs([lbreaki;sbreaki]));
end

worktimes = worktimes*24;


%% figure showing average working times for days of the week
wkdays = {'Mon','Tue','Wed','Thu','Fri','Sat','Sun'};

days = struct2cell(actdaily);
days = days(4,1,:);

wlabel = squeeze(cellfun(@(x) cstrfind(wkdays,datestr(x,'ddd')),days));

vis1 = initvis([]);

xx = (1:7)';
wdtimes = nan(7,3,2);
for w = 1:7
    wdtimes(w,:,1) = mean(worktimes(wlabel==w,:),1);
    wdtimes(w,:,2) = std(worktimes(wlabel==w,:),[],1);
end

vis1.bars = bar(xx,squeeze(wdtimes(:,2,1)));
hold on
for w = 1:7
    nw = sum(wlabel==w);
    if nw>0
        vis1.points1(w) = plot(xx(w)*ones(nw,1),worktimes(wlabel==w,2),'.r');
    end
end
% vis1.errbars = errorbar(xx',squeeze(wdtimes(:,2,1)),2*squeeze(wdtimes(:,2,2)));
% set(vis1.errbars,'LineStyle','none','Color','k')

xlim([0,8])
ylim([0,10.5])

set(vis1.bars,'FaceColor',[.8 .9 .9])
set(vis1.points1,'Color', [.6 .2  0])

set(gca,'XTick',1:7,'XTickLabel',wkdays)
xlabel('day of the week')
ylabel('average working time in hours')


%% average weekly working hours
% get all recorded days
days = struct2cell(actdaily);
days = squeeze(cell2mat(days(4,1,:)));

% find first Monday
for d1 = 1:ndays
    if weekday(days(d1)) == 2
        break
    end
end

% find last Friday
for dend = ndays : -1 : 1
    if weekday(days(dend)) == 6
        break
    end
end

% span all weeks in between and reshape per week
alldays = days(d1) : days(dend) + 2;
nweeks = numel(alldays) / 7;
alldays = reshape(alldays, [7, nweeks])';

% get working time for each week (set to nan, if incomplete)
weeklyworktime = nan(nweeks,1);
fullweek = false(nweeks,1);
for w = 1:nweeks
    weekdays = find( ismember(days, alldays(w, :)) );
    weeklyworktime(w) = sum( worktimes(weekdays, 2) );
    
    weekdays = sort( days(weekdays) );
    if numel(weekdays) > 4 && weekday( weekdays(1) ) == 2 && weekday( weekdays(5) ) == 6
        fullweek(w) = true;
    end
end

% average
meanweeklyworktime = mean( weeklyworktime(fullweek) );

% plot histogram
figure
hist( weeklyworktime(fullweek) )
title( sprintf('mean = %4.2f', meanweeklyworktime) )
xlabel('weekly working hours')


%% time spent in different meetings compared to netto working time
%  this excludes any preparation time or post-processing time
meetcls = {'instmeet','grmeet','indmeet'};
ncls = length(meetcls);

minds = cell(1,ncls);
mdurs = nan(1,ncls);
for i = 1:ncls
    minds{i} = cstrfind(actall.acts,acls.(meetcls{i}));
    mdurs(i) = sum(actall.durs(minds{i}));
end

vis2 = initvis([],[680   800   950   300]);

subplot(1,3,3)
vis2.pie3 = pie(mdurs);
title('different meetings (incl. preptime)')
legend({'institute-wide','grouplevel','individuals'},'Location','SouthOutside')

minds = cell(1,ncls);
mdurs = nan(1,ncls);
for i = 1:ncls
    mcls = cell(1,length(acls.(meetcls{i})));
    for j = 1:length(acls.(meetcls{i}))
        mcls{j} = ['^',acls.(meetcls{i}){j}];
    end
    minds{i} = cstrfind(actall.acts,mcls);
    mdurs(i) = sum(actall.durs(minds{i}));
end

total = sum(worktimes(:,3))/24; % total in days

subplot(1,3,1)
vis2.pie1 = pie([total-sum(mdurs),sum(mdurs)],[0,1]);
title('time spent in all kinds of meetings')
legend({'other work','meetings'},'Location','SouthOutside')

subplot(1,3,2)
vis2.pie2 = pie(mdurs);
title('different meetings')
legend({'institute-wide','grouplevel','individuals'},'Location','SouthOutside')


%% time spent in meetings with individuals
indmeetacts = actall.acts(minds{cstrfind(meetcls,'indmeet')});
indmeetdurs = actall.durs(minds{cstrfind(meetcls,'indmeet')});

individ = struct([]);
for i = 1:length(indmeetacts)
    % regexp finding names after "meeting with"
    persons = regexp(indmeetacts{i},'(?<=meeting with )(\w+)(?:[ ,]?(?:and)? +(\w+))*','match');
    % extract names
    persons = regexp(persons,'\<(?!and)\w+','match');
    for p = 1:length(persons)
        if isfield(individ,persons{1}{p})
            individ.(persons{1}{p}) = individ.(persons{1}{p}) + indmeetdurs(i);
        else
            individ(1).(persons{1}{p}) = indmeetdurs(i);
        end
    end
end

individ = orderfields(individ);
individdurs = cell2mat(struct2cell(individ));
individname = fieldnames(individ);

vis3 = initvis([],[680 764 1050 340]);

vis3.bar = bar(individdurs*24);
xlabel('person')
ylabel('meeting time in hours')
set(gca,'XTick',1:length(individname),'XTickLabel',individname)
xticklabel_rotate


%% time spent working on "paper" (this is the rRNN paper)
% paper time vs. other time

% evolution of paper time per week


%% time spent on different projects
% what is a project name?
% project names mentioned in: deriving ... for , reading, literature
% search, making ... for , managing, preparing ... for , programming,
% coding, thinking about, writing ... for , 

% extract project names after occurrence of "for"
namestmp = regexp(actall.acts,'(?<=for )[\w \-]+\w','match','once');
projnames = namestmp(cstrfind(namestmp,'\w+'));
% extract additional project names after occurrence of coding
namestmp = regexp(actall.acts,'(?<=coding )(?!for )[\w \-]+\w','match','once');
projnames = unique([projnames(:);namestmp(cstrfind(namestmp,'\w+'))]);
namestmp = regexp(actall.acts,'(?<=programming )(?!for )[\w \-]+\w','match','once');
projnames = unique([projnames(:);namestmp(cstrfind(namestmp,'\w+'))]);
% extract additional project names after occurrence of thinking about
namestmp = regexp(actall.acts,'(?<=thinking about )[\w \-]+\w','match','once');
projnames = unique([projnames(:);namestmp(cstrfind(namestmp,'\w+'))]);

% assumption is that the above was sufficient to find all project names

% exclude meeting names by hand, because they are not projects
% leave names of individuals in, because they stand for something that I
% have done for the individuals probably for a particular project
projnames = setdiff(projnames,[acls.grmeet(:);acls.instmeet(:)]);
nproj = length(projnames);

% equivalence between project names: 
% [speeddem, dem, free energy]
% [general, background]
% [rrnns, fernns]
% [placecells, eduardo]
% [kai, kai dannies]
% [mbpdm paper, mb-pdm paper, pdecision paper]
% these project names will be replaced:
prjeq = {'dem','free energy','background',...
         'fernns','eduardo','pdecision', 'kai', 'mb-pdm paper', 'pdecision paper', 'dbpdm paper'};
projNames = setdiff(projnames,prjeq);
prji = nan(nproj,1);
for p = 1:nproj
    switch projnames{p}
        case {'dem','free energy'}
            prji(p) = cstrfind(projNames,'speeddem');
        case 'background'
            prji(p) = cstrfind(projNames,'general');
        case 'fernns'
            prji(p) = cstrfind(projNames,'rrnns');
        case 'eduardo'
            prji(p) = cstrfind(projNames,'placecells');
        case 'pdecision'
            prji(p) = cstrfind(projNames,'pdecisions');
        case {'kai dannies'}
            prji(p) = cstrfind(projNames,'kai');
        case {'mb-pdm paper', 'pdecision paper', 'dbpdm paper'}
            prji(p) = cstrfind(projNames,'mbpdm paper');
        otherwise
            tmp = cstrfind(projNames,projnames{p});
            assert(numel(tmp)==1, 'assertion failed: the title of a project occurs inside another project title')
            prji(p) = tmp;
    end
end
nprojeq = length(projNames);

% find all weeks:
% find first Monday
for d = 1:10
    if weekday(actdays(d))==2
        break
    end
end
d1 = d;

% find last Friday
for d = 0:10
    if weekday(actdays(end-d))==6
        break
    end
end
dend = ndays-d;

% how many weeks are there?
nweeks = ceil((actdays(dend)-actdays(d1))/7);

% find all activities associated with found projects
projfracs = zeros(nweeks,nprojeq+1); % one additional entry for groupmeetings
for w = 1:nweeks
    dweek = actdays(d1) + (w-1)*7;
    dweek = find(actdays>=dweek & actdays<dweek+7);
    if ~isempty(dweek)
        % concatenate all activities of that week
        actweek = cell(200,1);
        dursweek = nan(200,1);
        cnt = 0;
        for d = dweek
            na = size(actdaily(d).durs,1);
            actweek(cnt+(1:na)) = lower(actdaily(d).acts);
            dursweek(cnt+(1:na)) = actdaily(d).durs;
            cnt = cnt + na;
        end
        actweek = actweek(1:cnt);
        dursweek = dursweek(1:cnt);
        
        weekdurs = zeros(1,nprojeq+1);
        weekdurs(end) = sum(dursweek(cstrfind(actweek,acls.grmeet)));
        
        % get project durations for that week
        % note that this is the simplest way of selecting project
        % durations simply by the occurrence of the project name, but it is
        % not always the case that the project name leads to a project,
        % e.g.: "meeting with Burak" could have been about anything, it
        % appears to be a reasonably good heuristic though, because these
        % things usually have a short duration compared to actual projects
        for p = 1:nproj
            weekdurs(prji(p)) = weekdurs(prji(p)) + ...
                sum(dursweek(cstrfind(actweek,projnames{p})));
        end
        projfracs(w,:) = weekdurs/sum(weekdurs);
    end
end

% a figure about the weekly fractions of time I spent in different projects
vis = initvis([],[140  680 1700 420]);
vis.bars = bar(projfracs,1,'stacked');
ylim([0,1])
xlim([0.5,nweeks+.5])

legend([projNames,{'groupmeetings'}],'Location','EastOutside')
xlabel('weeks')
ylabel('fraction of project time')


%% show activities of a particular week
w = 47;
dweek = actdays(d1) + (w-1)*7;
dweek = find(actdays>=dweek & actdays<dweek+7);

% concatenate all activities of that week
actweek = cell(200,1);
dursweek = nan(200,1);
cnt = 0;
for d = dweek
    na = size(actdaily(d).durs,1);
    actweek(cnt+(1:na)) = lower(actdaily(d).acts);
    dursweek(cnt+(1:na)) = actdaily(d).durs;
    cnt = cnt + na;
end
actweek = actweek(1:cnt);
dursweek = dursweek(1:cnt);


%% distribution of starting and feierabend times
startt = nan(ndays,1);
endt = nan(ndays,1);
for d = 1:ndays
    startt(d) = rem(actdaily(d).times(1),1)*24;
    endt(d) = rem(actdaily(d).times(end),1)*24;
end

vis = initvis([],[370   810   950   300]);

subplot(1,2,1)
xx = [floor(min(startt)*4),ceil(max(startt)*4)]/4;
xx = xx(1)+0.125:.25:xx(2);
[num,xout] = hist(startt,xx);
vis.bar1 = bar(xout,num,1);
set(vis.bar1,'FaceColor',[.95 .95 .8],'EdgeColor',[.2 .6 .2])
ylabel('number of days')
xlabel('hour of day')
title('start of working day')
xl = xlim;
set(gca,'XTick',round(xl(1)):round(xl(2)))

subplot(1,2,2)
xx = [floor(min(endt)*4),ceil(max(endt)*4)]/4;
xx = xx(1)+0.125:.25:xx(2);
[num,xout] = hist(endt,xx);
vis.bar2 = bar(xout,num,1);
set(vis.bar2,'FaceColor',[0 0 .5],'EdgeColor',[.8 .8 .1])
ylabel('number of days')
xlabel('hour of day')
title('feierabend')
xl = xlim;
set(gca,'XTick',round(xl(1)):round(xl(2)))


%% proportion of time spent on different activities (weekly)
% THERE MUST BE A BUG SOMEWHERE HERE!!!

% find all weeks:
% find first Monday
for d = 1:10
    if weekday(actdays(d))==2
        break
    end
end
d1 = d;

% find last Friday
for d = 0:10
    if weekday(actdays(end-d))==6
        break
    end
end
dend = ndays-d;

% how many weeks are there?
nweeks = ceil((actdays(dend)-actdays(d1))/7);

% collect weekly activities
actfracs = zeros(nweeks,nacls);
for w = 1:nweeks
    dweek = actdays(d1) + (w-1)*7;
    dweek = find(actdays>=dweek & actdays<dweek+7);
    if ~isempty(dweek)
        % concatenate all activities of that week
        actweek = cell(200,1);
        dursweek = nan(200,1);
        cnt = 0;
        for d = dweek
            na = size(actdaily(d).durs,1);
            actweek(cnt+(1:na)) = lower(actdaily(d).acts);
            dursweek(cnt+(1:na)) = actdaily(d).durs;
            cnt = cnt + na;
        end
        actweek = actweek(1:cnt);
        dursweek = dursweek(1:cnt);
        
        weekdurs = zeros(1,nacls);
        weekdurs(end) = sum(dursweek(cstrfind(actweek,acls.grmeet)));
        
        [sbreaki,lbreaki] = findBreaks(actweek,acls.smbreak,acls.bgbreak,dursweek);
        weekdurs(1) = sum(dursweek(lbreaki));
        weekdurs(2) = sum(dursweek(sbreaki));
        
        % get activity durations for that week
        for c = 3:nacls
            assert(~strcmp(aclsnames{c},'smbreak'))
            aclsc = cellfun(@(x) ['^',x], acls.(aclsnames{c}), 'UniformOutput', 0);
            weekdurs(c) = weekdurs(c) + sum(dursweek(cstrfind(actweek,aclsc)));
        end
        actfracs(w,:) = weekdurs/sum(weekdurs);
    end
end

% a figure about the weekly fractions of time I spent on different activities
vis = initvis([],[140  680 1700 420]);
vis.bars = bar(actfracs,1,'stacked');
ylim([0,1])
xlim([0.5,nweeks+.5])

legend(aclsnames,'Location','EastOutside')
xlabel('weeks')
ylabel('fraction of working time')