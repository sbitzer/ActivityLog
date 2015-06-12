# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 19:07:49 2014

@author: Sebastian Bitzer (official@sbitzer.eu)
"""

import sqlite3
import re
import itertools
import datetime as dt
import cmd
import random
import sys


def isSQLite3(filename):
    from os.path import isfile, getsize

    if not isfile(filename):
        return -1
    if getsize(filename) < 100: # SQLite database file header is 100 bytes
        return 0
    else:
        fd = open(filename, 'rb')
        Header = fd.read(100)
        fd.close()

        if Header[0:16] == b'SQLite format 3\000':
            return 1
        else:
            return 0

def writeTestEntries(alog):
    alog.dbcur.execute(
        "INSERT INTO activities (name, label) VALUES('email', 'email')")
    alog.dbcur.execute(
        "INSERT INTO activities (name, label) VALUES('break', 'break')")
    alog.dbcur.execute(
        "INSERT INTO activities (name, label) VALUES('lunch', 'lunch')")
    alog.dbcur.execute(
        "INSERT INTO projects (name, label) VALUES('BeeExp', 'BeeExp')")
    alog.dbcur.execute(
        "INSERT INTO projects (name, label) VALUES('Bayesian attractor model', 'BAttM')")
    alog.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('email', 'activities', 2)")
    alog.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('small break', 'activities', 3)")
    alog.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('break', 'activities', 3)")
    alog.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('lunch', 'activities', 4)")
    alog.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('BeeExp', 'projects', 1)")
    alog.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('BeeExperiment', 'projects', 1)")
    alog.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('BAttM', 'projects', 2)")

    now = dt.datetime.now()
    for i in range(7):
        dur = random.random() * 1000
        datetime = now + dt.timedelta(minutes = 2*i - 2*7)
        alog.dbcur.execute(
            "INSERT INTO jobs (start, duration, activity) VALUES (?, ?, 2)",
            (datetime, dur))

    alog.dbcon.commit()


class ActivityLog(cmd.Cmd):
    """A class which defines and manipulates an activity log"""

    # this separates the three parts of a job string:
    # activity[ with people][ for project|org|person]
    act_re = re.compile('([\w\- ]+?)(?: with ([\w\- ,]+?))?(?:$| (?:fro|for|about) ([\w\- ,]+))')
    time_re = re.compile('([\w\- ,]+)?(?:@(\d+):(\d+)(?::(\d+))?)?')

    # [id of last row in jobs, its start timestamp, its duration]
    lastjob = [None, None, None]

    dbname = None

    def __init__(self, dbname):
        cmd.Cmd.__init__(self)

        dbstate = isSQLite3(dbname)
        if dbstate == 1:
            self.dbcon = sqlite3.connect(dbname, detect_types=sqlite3.PARSE_DECLTYPES)
            self.dbcur = self.dbcon.cursor()
            self.dbcur.execute("PRAGMA foreign_keys = ON")

            self.init_lastjob()
            self.checkLastDuration()
        elif dbstate == 0:
            raise IOError(77, 'The file name points to a file that does not appear to be an SQLite3 database', dbname)
        else:
            ans = raw_input('No file with that name exists. Make new database (y/n)? ')
            if ans.lower() == 'y':
                self.dbcon = sqlite3.connect(dbname, detect_types=sqlite3.PARSE_DECLTYPES)
                self.dbcur = self.dbcon.cursor()
                self.dbcur.execute("PRAGMA foreign_keys = ON")

                self.initDB()
            else:
                self.dbcon = None

        self.dbname = dbname


    def __del__(self):
        self.dbcon.close()


    def init_lastjob(self):
        """find the newest job in DB and use this as lastjob"""
        now = dt.datetime.now()
        self.dbcur.execute("SELECT id, start, duration FROM jobs "
            "WHERE start < ? ORDER BY start DESC", (now, ))
        self.lastjob = self.dbcur.fetchone()

        if self.lastjob == None:
            self.lastjob = [None, None, None]
        else:
            self.lastjob = list(self.lastjob)


    def initDB(self):
        """Creates a database with the predefined schema."""

        self.dbcur.execute(
            "CREATE TABLE activities ("
                "id INTEGER PRIMARY KEY,"
                "name TEXT UNIQUE NOT NULL,"
                "label TEXT UNIQUE NOT NULL )" )

        self.dbcur.execute(
            "CREATE TABLE organisations ("
                "id INTEGER PRIMARY KEY,"
                "name TEXT UNIQUE NOT NULL,"
                "label TEXT UNIQUE NOT NULL )" )

        self.dbcur.execute(
            "CREATE TABLE people ("
                "id INTEGER PRIMARY KEY,"
                "name TEXT UNIQUE NOT NULL,"
                "label TEXT UNIQUE NOT NULL,"
                "org INTEGER,"
                "FOREIGN KEY(org) REFERENCES organisations(id) )" )

        self.dbcur.execute(
            "CREATE TABLE projects ("
                "id INTEGER PRIMARY KEY,"
                "name TEXT UNIQUE NOT NULL,"
                "label TEXT UNIQUE NOT NULL,"
                "org INTEGER,"
                "FOREIGN KEY(org) REFERENCES organisations(id) )" )

        # this table stores default activities for projects which are used in
        # job strings without an activity
        self.dbcur.execute(
            "CREATE TABLE pj_defact ("
                "project INTEGER PRIMARY KEY,"
                "activity INTEGER,"
                "FOREIGN KEY(project) REFERENCES projects(id),"
                "FOREIGN KEY(activity) REFERENCES activities(id) )" )

        # This is a dictionary which stores alternative strings used to
        # describe the same entity in the database. Strictly, there are
        # foreign key constraints on the tab_id, but because I chose to use a
        # compact storage format in which the alternative strings may refer to
        # entities from any of the tables, I cannot implement the foreign key
        # constraints with SQL syntax.
        self.dbcur.execute(
            "CREATE TABLE dictionary ("
                "word TEXT PRIMARY KEY,"
                "tab_name TEXT NOT NULL,"
                "tab_id INTEGER NOT NULL )" )

        # the main table storing time-logged jobs
        self.dbcur.execute(
            "CREATE TABLE jobs ("
                "id INTEGER PRIMARY KEY,"
                "start TIMESTAMP NOT NULL UNIQUE,"
                "duration REAL,"
                "activity INTEGER NOT NULL,"
                "FOREIGN KEY(activity) REFERENCES activities(id) )" )

        # the following tables implement possible one-to-many relationships
        # between jobs and people, projects and organisations

        self.dbcur.execute(
            "CREATE TABLE job_p ("
                "job INTEGER,"
                "person INTEGER,"
                "PRIMARY KEY(job, person),"
                "FOREIGN KEY(job) REFERENCES jobs(id),"
                "FOREIGN KEY(person) REFERENCES people(id) )" )

        self.dbcur.execute(
            "CREATE TABLE job_pj ("
                "job INTEGER,"
                "project INTEGER,"
                "PRIMARY KEY(job, project),"
                "FOREIGN KEY(job) REFERENCES jobs(id),"
                "FOREIGN KEY(project) REFERENCES projects(id) )" )

        self.dbcur.execute(
            "CREATE TABLE job_org ("
                "job INTEGER,"
                "org INTEGER,"
                "PRIMARY KEY(job, org),"
                "FOREIGN KEY(job) REFERENCES jobs(id),"
                "FOREIGN KEY(org) REFERENCES organisations(id) )" )

        self.dbcur.execute(
            "INSERT INTO activities (name, label) VALUES('default activity', 'mixed')")
        self.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('mixed', 'activities', 1)")
        self.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('default', 'activities', 1)")
        self.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('default activity', 'activities', 1)")

        self.dbcon.commit()

#        writeTestEntries(self)

    # print a job from the DB
    def printJob(self, jobid):
        if jobid == None:
            print "No job to print."
        else:
            # get info from DB
            self.dbcur.execute(
                "SELECT activity, start, duration FROM jobs "
                "WHERE id = ?", (jobid,))
            job = self.dbcur.fetchone()
            if job == None:
                print "Job requested to print does not exist."
            else:
                startstr = job[1].strftime('%Y-%m-%d %H:%M')
                if job[2] == None:
                    endstr = 'running ...'
                else:
                    endstr = (job[1] + dt.timedelta(seconds = job[2])).strftime('%Y-%m-%d %H:%M')
                    endstr = endstr + " (~%d min)" % (job[2] / 60)

                # get name of activity from DB
                self.dbcur.execute(
                    "SELECT name FROM activities "
                    "WHERE id = ?", (job[0],))
                jobstr = self.dbcur.fetchone()
                if jobstr == None:
                    jobstr = "Did not find name of activity with id %d" % job[0]
                else:
                    jobstr = jobstr[0]

                print startstr + " -> " + endstr + ": " + jobstr


    def addBaseType(self, name, table):
        corrinput = False

        while not corrinput:
            response = raw_input("label/organisation (or type help): ")
            if response.strip().lower() == "help":
                response = raw_input("You can now provide a shorter version of %s as label, \n"
                    "if you wish. If you currently add a person or project\n"
                    "to the database, you may assign that to an organisation.\n"
                    "Provide this as 'label & organisation'! You can leave\n"
                    "anyone of them empty as long as you provide the '&'.\n"
                    "Simply press ENTER to use %s as label and no organisation:\n"
                    % (name, name))

            if response == '':
                corrinput = True
                label = name
                org = None
            else:
                match = re.match('([\w\- ]*)(?:&([\w\- ]*))?', response)
                if match == None:
                    print("DID NOT RECOGNISE FORMAT!\n"
                          "Make sure you follow the instructions below!\n"
                          "Only use alpha-numeric names without spaces on either side of the &!\n\n")
                    continue
                else:
                    corrinput = True

                    if match.group(1) == None:
                        label = name
                    else:
                        label = match.group(1).strip()

                    if match.group(2) == None:
                        org = None
                    else:
                        org = self.getIDfromDict(match.group(2).strip(), 'organisations')

        # may FAIL because label not unique!
        try:
            if (table == 'people' or table == 'projects') and not org == None:
                self.dbcur.execute(
                    "INSERT INTO '%s' (name, label, org) "
                    "VALUES(?, ?, ?)" % table, (name, label, org[0]))
            else:
                self.dbcur.execute(
                    "INSERT INTO '%s' (name, label) "
                    "VALUES(?, ?)" % table, (name, label))
        except sqlite3.IntegrityError as interr:
            if interr.message == 'column label is not unique':
                self.dbcur.execute(
                    "SELECT name "
                    "FROM '%s' "
                    "WHERE label = ?" % table, (label,) )
                exname = self.dbcur.fetchone()
                exname = exname[0]

                print "Label needs to be unique!"
                print "Your label '%s' is already used by '%s'." % (label, exname)
                print "Please provide a new label."
                newid = self.addBaseType(name, table)
            else:
                raise interr
        else:
            self.dbcon.commit()

            newid = self.dbcur.lastrowid

            # add also to dictionary
            self.dbcur.execute(
                "INSERT INTO dictionary (word, tab_name, tab_id) "
                "VALUES(?, ?, ?)", (name, table, newid))

            self.dbcon.commit()

        return newid


    def resolveUnknownName(self, name, table):
        if len(table) > 1:
            tabstr = '0: %s' % table[0]
            for i, tab in enumerate(table[1:]):
                tabstr = tabstr + ', %d: %s' % (i+1, tab)

            response = raw_input("Does %s belong into %s?:\n" % (name, tabstr))
            table = table[int(response)]
        else:
            table = table[0]

        response = raw_input("%s unknown. Resolve (or type help): " % name)
        if response.strip().lower() == "help":
            # misspelled, new alias, or new entry?
            response = raw_input("There is no %s in %s. Add in %s (1),\n"
                "add as alias (2: realname) or check DB (3)? If you\n"
                "made a typo, you can also just provide the name again\n"
                "without the typo:\n" % (name, table, table))

        if response[0] == '1':
            return (self.addBaseType(name, table), table)
        elif response[0] == '2':
            nameintab = response[2:].strip()
            idtab = self.getIDfromDict(nameintab, table)
            self.dbcur.execute(
                "INSERT INTO dictionary (word, tab_name, tab_id) "
                "VALUES(?, ?, ?)", (name, table, idtab[0]))
            self.dbcon.commit()

            return idtab
        elif response[0] == '3':
            # print all table entries repeating those in the end that start
            # with the same letters and redo
            self.dbcur.execute(
                "SELECT name, label "
                "FROM '%s'"
                "ORDER BY name ASC" % table )
            namelist = self.dbcur.fetchall()

            for (dbname, dblabel) in namelist:
                print '%15s: %s' % (dblabel, dbname)

            return self.resolveUnknownName(name, (table,))
        else:
            return self.getIDfromDict(response.strip(), table)


    def getIDfromDict(self, name, table):
        if name == None:
            return None

        if type(table).__name__ == 'str':
            table = (table,)

        # because table may have several values I have to construct an IN
        # statement with variable number of elements (?) inside paranthesis
        placeholders = ','.join('?' for unused in table)
        self.dbcur.execute(
            "SELECT tab_id, tab_name "
            "FROM dictionary "
            "WHERE word = ? and tab_name IN (%s)" % placeholders, (name,)+ table )
        result = self.dbcur.fetchone()
        if result == None:
            # name is not in dictionary:
            return self.resolveUnknownName(name, table)
        else:
            return result


    def parsePeople(self, pstr):
        # returns a list of people IDs from the database given a string of
        # people in the format A (,|and) B (,|and) ...

        namelist = map( lambda s: s.split(', '), pstr.split(' and ') )
        namelist = list( itertools.chain.from_iterable(namelist) )

        idlist = []
        for name in namelist:
            idtab = self.getIDfromDict(name, 'people')
            idlist.append(idtab[0])

        return idlist


    def parseForinfo(self, forstr):

        # project-person-organisation list
        ppolist = map( lambda s: s.split(', '), forstr.split(' and ') )
        ppolist = list( itertools.chain.from_iterable(ppolist) )

        pids = []
        pjids = []
        orgids = []
        for ppo in ppolist:
            forid, fortab = self.getIDfromDict(ppo.strip(), ('projects', 'people',
                                                     'organisations'))

            if fortab == 'projects':
                pjids.append(forid)
            elif fortab == 'people':
                pids.append(forid)
            else:
                orgids.append(forid)

        if len(pjids) == 0:
            pjids = None
        if len(orgids) == 0:
            orgids = None

        return pjids, pids, orgids


    def setDefaultActivity(self, projectid):
        self.dbcur.execute(
            "SELECT name "
            "FROM projects "
            "WHERE id = ?", (projectid,) )
        pjname = self.dbcur.fetchone()
        pjname = pjname[0]

        response = raw_input("Default activity for project '%s'\n"
            "(or type help): " % pjname)
        if response.strip().lower() == "help":
            response = raw_input("You logged project '%s' in place\n"
                "of an activity. Whenever you do that the job will\n"
                "be logged with a default activity associated with\n"
                "the project. What activity should that be? Simply\n"
                "press Enter, if you want to use the default 'mixed'\n"
                "activity as your default!:\n" % pjname)
        if response == '':
            response = 'mixed'

        actid = self.getIDfromDict(response, 'activities')
        self.dbcur.execute(
            "INSERT INTO pj_defact (project, activity) "
            "VALUES(?, ?)", (projectid, actid[0]))
        self.dbcon.commit()

        return actid[0]


    def getDefaultActivity(self, projectid):
        self.dbcur.execute(
            "SELECT activity "
            "FROM pj_defact "
            "WHERE project = ?", (projectid,) )

        result = self.dbcur.fetchone()
        if result == None:
            # this project has no default activity, yet
            return self.setDefaultActivity(projectid)
        else:
            return result[0]


    def parseJobStr(self, jobstr):
        """parses the raw input from the user"""

        # act(e.g. break)
        # act(e.g. meeting) with {people}
        # act(e.g. meeting) with {people} for {project|org|person}
        # act(e.g. reading) for {project|org|person}
        # act(e.g. thinking) about {people|projects}

        # extract activity and modifier
        match = self.act_re.match(jobstr)

        act = None
        people = None
        orgs = None
        projects = None

        if match != None:
            if match.group(3) != None:
                projects, person, orgs = self.parseForinfo(match.group(3))
            else:
                person = []

            actpj, tab = self.getIDfromDict(match.group(1).strip(), ('activities',
                                            'projects'))

            # if a project name was used in place of an activity
            if tab == 'projects':
                # get the default activity for this project
                act = self.getDefaultActivity(actpj)

                if projects == None:
                    projects = [actpj]
                else:
                    projects.append(actpj)
            else:
                act = actpj

            if match.group(2) != None:
                people = self.parsePeople(match.group(2))
            else:
                people = []

            people = people + person
            if len(people) == 0:
                people = None

        return act, people, projects, orgs


    def addJobToDB(self, startdt, act, projects=None, people=None, orgs=None):
        # add job to jobs table and retrieve its id
        self.dbcur.execute(
            "INSERT INTO jobs (start, activity) "
            "VALUES(?, ?)", (startdt, act) )
        jobid = self.dbcur.lastrowid

        # add associated project(s), if exist
        if projects != None:
            for pjid in projects:
                self.dbcur.execute(
                    "INSERT INTO job_pj (job, project) "
                    "VALUES(?, ?)", (jobid, pjid) )

        # add associated organisation(s), if exist
        if orgs != None:
            for oid in orgs:
                self.dbcur.execute(
                    "INSERT INTO job_org (job, org) "
                    "VALUES(?, ?)", (jobid, oid) )

        # add associated people, if exist
        if people != None:
            for pid in people:
                self.dbcur.execute(
                    "INSERT INTO job_p (job, person) "
                    "VALUES(?, ?)", (jobid, pid) )

        self.dbcon.commit()

        return jobid


    def addDurationToJob(self, enddt):

        if self.lastjob[0] != None:
            if self.lastjob[2] == None:
                duration = (enddt - self.lastjob[1]).total_seconds()

                # everything is fine
                if duration >= 0:
                    self.dbcur.execute(
                        "UPDATE jobs SET duration=? WHERE id=?", (duration,
                                                                  self.lastjob[0]))

                    self.dbcon.commit()
                    self.lastjob[2] = duration

                # resolve impossible negative duration by asking user
                else:
                    validtime = False

                    # get start time of job previous to lastjob
                    self.dbcur.execute("SELECT id, start FROM jobs WHERE id < ? "
                        "ORDER BY start DESC", (self.lastjob[0],))
                    oldjob = self.dbcur.fetchone()

                    while not validtime:
                        response = raw_input("Negative duration! Fix (or type help): ")

                        # help needed
                        if response.strip().lower() == "help":
                            response = raw_input("From the given times the last job has a negative\n"
                            "duration. This cannot be. Please provide a new time.\n"
                            "To provide a new time for the new input just give the\n"
                            "time with an @. To provide a new time for the last input\n"
                            "prepend the time with the word 'last'! Note that, if you\n"
                            "choose to change the last input, the new time must be \n"
                            "between %02d:%02d and %02d:%02d. Syntax examples:\n"
                            "last @12:34\n"
                            "@14:49\n" % (oldjob[1].hour, oldjob[1].minute,
                                          enddt.hour, enddt.minute))

                        # extract time
                        match = self.time_re.match(response)

                        # invalid format
                        if ( match == None or match.group(2) == None or
                            match.group(3) == None ):
                            print "Given input has invalid format!\n"
                        else:
                            hours = int(match.group(2))
                            mins = int(match.group(3))
                            if hours < 0 or hours >= 24 or mins < 0 or mins >= 60:
                                print "Given time is invalid!\n"
                                continue

                            # time only: change enddt
                            if match.group(1) == None:
                                enddt = dt.datetime.combine(enddt.date(),
                                                            dt.time(hours, mins))
                                if enddt >= self.lastjob[1]:
                                    validtime = True
                                    self.addDurationToJob(enddt)
                                else:
                                    print "New time is still before start of last job!\n"

                            # last: change time of lastjob
                            elif match.group(1).strip() == 'last':
                                # is new time between oldstart and enddt?
                                newdt = dt.datetime.combine(self.lastjob[1].date(),
                                                            dt.time(hours, mins))
                                if oldjob[1] <= newdt and newdt <= enddt:
                                    validtime = True

                                    # update lastjob start in DB and self.lastjob
                                    self.lastjob[1] = newdt
                                    self.dbcur.execute("UPDATE jobs SET start=? WHERE id=?",
                                                       (newdt, self.lastjob[0]))

                                    # update duration of job with oldid in DB
                                    duration = (newdt - oldjob[1]).total_seconds()
                                    self.dbcur.execute("UPDATE jobs SET duration=? "
                                        "WHERE id=?", (duration, oldjob[0]))

                                    self.dbcon.commit()

                                    self.addDurationToJob(enddt)
                                else:
                                    print "New time is not between %02d:%02d and %02d:%02d!\n" % (
                                        oldjob[1].hour, oldjob[1].minute,
                                        enddt.hour, enddt.minute)
            else:
                oldenddt = self.lastjob[1] + dt.timedelta(seconds = self.lastjob[2])
                if oldenddt > enddt:
                    validtime = False
                    while not validtime:
                        response = raw_input("Start time of new job is before\n"
                            "end time of last job. Fix (or type help):")

                        # help needed
                        if response.strip().lower() == "help":
                            response = raw_input("From the given times the new job starts\n"
                            "before the last job ends. This cannot be.\n"
                            "Please provide a new time.\n"
                            "To provide a new start time of the new job just give the\n"
                            "time with an @. To provide a new end time for the last job\n"
                            "prepend the time with the word 'last'! Note that, if you\n"
                            "choose to change the last job, the new time must be \n"
                            "between %02d:%02d and %02d:%02d. Syntax examples:\n"
                            "last @12:34\n"
                            "@14:49\n" % (self.lastjob[1].hour, self.lastjob[1].minute,
                                          enddt.hour, enddt.minute))

                        # extract time
                        match = self.time_re.match(response)

                        # invalid format
                        if ( match == None or match.group(2) == None or
                            match.group(3) == None ):
                            print "Given input has invalid format!\n"
                        else:
                            hours = int(match.group(2))
                            mins = int(match.group(3))
                            if hours < 0 or hours >= 24 or mins < 0 or mins >= 60:
                                print "Given time is invalid!\n"
                                continue

                            # time only: change enddt
                            if match.group(1) == None:
                                enddt = dt.datetime.combine(enddt.date(),
                                                            dt.time(hours, mins))
                                if enddt >= oldenddt:
                                    validtime = True
                                else:
                                    print "New start time is still before end time of last job!\n"

                            # last: change time of lastjob
                            elif match.group(1).strip() == 'last':
                                # is new end time of last job between oldstart and enddt?
                                newenddt = dt.datetime.combine(self.lastjob[1].date(),
                                                            dt.time(hours, mins))
                                if self.lastjob[1] <= newenddt and newenddt <= enddt:
                                    validtime = True

                                    duration = (newenddt - self.lastjob[1]).total_seconds()

                                    self.lastjob[2] = duration
                                    self.dbcur.execute("UPDATE jobs SET duration=? "
                                        "WHERE id=?", (duration, self.lastjob[0]))

                                    self.dbcon.commit()
                                else:
                                    print "New end time of last job is not between %02d:%02d and %02d:%02d!\n" % (
                                        self.lastjob[1].hour, self.lastjob[1].minute,
                                        enddt.hour, enddt.minute)

        return enddt


    def checkLastDuration(self):
        if self.lastjob[0] != None and self.lastjob[2] == None:
            addenddt = True

            enddt = dt.datetime.now()

            while True:
                response = raw_input("Last job has no duration.\n"
                    "continue last job (just press enter), \n"
                    "register follow-up job as usual (type job string), \n"
                    "provide end time as '@hours:mins' (today's date is used), \n"
                    "or check information about last job (type 'last'):\n")

                if response == '':
                    addenddt = False
                    break
                elif response.strip().lower() == 'last':
                    self.printJob(self.lastjob[0])
                else:
                    # extract time
                    match = self.time_re.match(response)

                    # invalid format
                    if ( match == None or match.group(2) == None or
                        match.group(3) == None ):
                        print "Given input has invalid format!\n"
                    elif match.group(1) == None:
                        hours = int(match.group(2))
                        mins = int(match.group(3))
                        if hours < 0 or hours >= 24 or mins < 0 or mins >= 60:
                            print "Given time is invalid!\n"
                        else:
                            enddt = dt.datetime.combine(enddt.date(),
                                                        dt.time(hours, mins))
                            break
                    else:
                        addenddt = False
                        self.default(response)
                        break

            if addenddt:
                self.addDurationToJob(enddt)


    def processJob(self, datetime, jobstr):
        act, people, projects, orgs = self.parseJobStr(jobstr)

        jobid = self.addJobToDB(datetime, act, projects, people, orgs)

        return jobid


    def getTime(self, instr):
        indt = dt.datetime.today()

        match = self.time_re.match(instr)
        if match.group(1) == None:
            jobstr = None
        else:
            jobstr = match.group(1).strip()

        if match.group(2) != None:
            if match.group(4) == None:
                secs = 0
            else:
                secs = int(match.group(4))

            # check whether time is valid
            hours = int(match.group(2))
            mins = int(match.group(3))

            if (hours >= 0 and hours < 24 and mins >= 0 and mins < 60 and
                secs >= 0 and secs < 60):
                indt = dt.datetime.combine(dt.date.today(),
                                           dt.time(hours, mins, secs))
            else:
                print "invalid time: taking current time instead\n"

        indt = self.addDurationToJob(indt)

        return indt, jobstr


    # pre-loop for greetings / print hours for this day/week
    def preloop(self):
        self.do_hours('')


    # handling of standard activity input
    def default(self, instr):
        indt, jobstr = self.getTime(instr)

        if jobstr is None:
            print "Did not recognize command or valid job string, skipping!"
        else:
            # process job
            lastid = self.processJob(indt, jobstr)
            self.lastjob = [lastid, indt, None]

            print indt.strftime('%H:%M')


    # delete or overwrite previous jobs
    def do_del(self, instr):
        if self.lastjob[0] == None:
            print 'No previous job in database! Continuing without delete.'
        else:
            # get start time of job previous to lastjob
            self.dbcur.execute("SELECT id, start, duration FROM jobs "
                "WHERE start < ? "
                "ORDER BY start DESC", (self.lastjob[1],))
            prevjob = list(self.dbcur.fetchone())

            # delete all things connected to last job in job_p, job_pj, job_org
            self.dbcur.execute(
                "DELETE FROM job_p "
                "WHERE job = ?", (self.lastjob[0],))
            self.dbcur.execute(
                "DELETE FROM job_pj "
                "WHERE job = ?", (self.lastjob[0],))
            self.dbcur.execute(
                "DELETE FROM job_org "
                "WHERE job = ?", (self.lastjob[0],))
            # delete job last to prevent DB IntegrityError
            self.dbcur.execute(
                "DELETE FROM jobs "
                "WHERE id = ?", (self.lastjob[0],))
            # finally ask user whether user also wants to delete duration of
            # previous to lastjob
            response = raw_input("Also update duration of the job before the "
                "deleted one?\n"
                "(just press enter for yes, type anything else for no): ")
            if response == '':
                prevjob[2] = None
                self.dbcur.execute(
                    "UPDATE jobs SET duration=Null WHERE id=?", (prevjob[0],))

            self.dbcon.commit()

            # set self.lastjob to point to previous to last job
            self.lastjob = prevjob

            # call self.default(instr), if instr is not empty
            if len(instr) > 0:
                self.default(instr)


    # print working hours
    def do_hours(self, instr):
        today = dt.datetime.today()
        today = today.date()

        # working hours for today:
        # sum the duration of jobs, but exclude lunches and breaks > 10min
        self.dbcur.execute(
            "SELECT SUM(duration) FROM jobs "
            "WHERE start >= ? "
            "AND NOT activity IN ("
                "SELECT id FROM activities "
                "WHERE name IN ('lunch') )"
            "AND NOT ( "
                "activity IN ("
                    "SELECT id FROM activities "
                    "WHERE name IN ('break') )"
                "AND duration > 600 )", (today, ))
        hours = self.dbcur.fetchone()[0]
        if hours == None:
            hours = 0
        else:
            hours = hours / 60 / 60

        # working hours for this week
        self.dbcur.execute(
            "SELECT SUM(duration) FROM jobs "
            "WHERE start >= ? "
            "AND NOT activity IN ("
                "SELECT id FROM activities "
                "WHERE name IN ('lunch') )"
            "AND NOT ( "
                "activity IN ("
                    "SELECT id FROM activities "
                    "WHERE name IN ('break') )"
                "AND duration > 600 )", (today - dt.timedelta(today.weekday()), ))
        weekhours = self.dbcur.fetchone()[0]
        if weekhours == None:
            weekhours = 0
        else:
            weekhours = weekhours / 60 / 60

        print "today:     %5.2f hours" % hours
        print "this week: %5.2f hours" % weekhours


    # print last job
    def do_last(self, instr):
        self.printJob(self.lastjob[0])


    # close session
    def do_feierabend(self, instr):
        indt, jobstr = self.getTime(instr)

        self.do_hours('')

        return True


if __name__ == "__main__":
    alog = ActivityLog('test.sqlite')
    alog.cmdloop()

#    if alog.dbcon != None:
#        alog.dbcon.close()
