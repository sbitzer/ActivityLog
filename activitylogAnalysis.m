%% definition of classes of activities
acls.bgbreak  = {'lunch','coffee','golf','physio','cycling'};       % large break
acls.smbreak  = {'break','chat'};                         % small break
acls.instmeet = {'imaging meeting','institute colloquium','neurotk','workshop','guest lecture'}; % institute-wide meetings
acls.grmeet   = {'groupmeeting','labmeeting','dysco'};     % group meetings
acls.indmeet  = {'meeting with'};                         % meetings with individual persons
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
acls.manage   = {'managing'};
acls.thinking = {'thinking'};
acls.doc      = {'documenting'};
acls.writing  = {'writing','notes',acls.doc{:}}; %#ok<CCAT>


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
    
    assert(all(actdaily(d).durs>=0))
    
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
clsnames = fieldnames(acls);
inds = [];
for c = 1:length(clsnames)
    inds = [inds,cstrfind(actall.acts,acls.(clsnames{c}))]; %#ok<AGROW>
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
namestmp = regexp(actall.acts,'(?<=for )[\w ]+\w','match','once');
projnames = namestmp(cstrfind(namestmp,'\w+'));
% extract additional project names after occurrence of coding
namestmp = regexp(actall.acts,'(?<=coding )(?!for )[\w ]+\w','match','once');
projnames = unique([projnames(:);namestmp(cstrfind(namestmp,'\w+'))]);
namestmp = regexp(actall.acts,'(?<=programming )(?!for )[\w ]+\w','match','once');
projnames = unique([projnames(:);namestmp(cstrfind(namestmp,'\w+'))]);
% extract additional project names after occurrence of thinking about
namestmp = regexp(actall.acts,'(?<=thinking about )[\w ]+\w','match','once');
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
prjeq = {'dem','free energy','background',...
         'fernns','eduardo'};
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
        otherwise
            prji(p) = cstrfind(projNames,projnames{p});
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
w = 35;
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