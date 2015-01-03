# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 19:07:49 2014

@author: Sebastian Bitzer
"""

import sqlite3
import re
import itertools
import datetime as dt
import cmd
import random


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
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('email', 'activities', 1)")
    alog.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('small break', 'activities', 2)")
    alog.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('break', 'activities', 2)")
    alog.dbcur.execute(
        "INSERT INTO dictionary (word, tab_name, tab_id) VALUES('lunch', 'activities', 3)")
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
            "INSERT INTO jobs (start, duration, activity) VALUES (?, ?, 1)",
            (datetime, dur))

    alog.dbcon.commit()


class ActivityLog(cmd.Cmd):
    """A class which defines and manipulates an activity log"""

    # this separates the three parts of a job string:
    # activity[ with people][ for project|org|person]
    act_re = re.compile('([\w ]+?)(?: with ([\w ,]+?))?(?:$| (?:for|about) ([\w ,]+))')
    time_re = re.compile('([\w ,]+)?(?:@(\d+):(\d+))?')

    # (id of last row in jobs, start timestamp in that row)
    lastjob = (None, None)

    def __init__(self, dbname):
        cmd.Cmd.__init__(self)

        dbstate = isSQLite3(dbname)
        if dbstate == 1:
            self.dbcon = sqlite3.connect(dbname, detect_types=sqlite3.PARSE_DECLTYPES)
            self.dbcur = self.dbcon.cursor()
            self.dbcur.execute("PRAGMA foreign_keys = ON")
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


    def __del__(self):
        self.dbcon.close()


    def initDB(self):
        """Creates a database with the predefined schema."""

        self.dbcur.execute(
            "CREATE TABLE activities ("
                "id INTEGER PRIMARY KEY,"
                "name TEXT NOT NULL,"
                "label TEXT UNIQUE NOT NULL )" )

        self.dbcur.execute(
            "CREATE TABLE organisations ("
                "id INTEGER PRIMARY KEY,"
                "name TEXT NOT NULL,"
                "label TEXT UNIQUE NOT NULL )" )

        self.dbcur.execute(
            "CREATE TABLE people ("
                "id INTEGER PRIMARY KEY,"
                "name TEXT NOT NULL,"
                "label TEXT UNIQUE NOT NULL,"
                "org INTEGER,"
                "FOREIGN KEY(org) REFERENCES organisations(id) )" )

        self.dbcur.execute(
            "CREATE TABLE projects ("
                "id INTEGER PRIMARY KEY,"
                "name TEXT NOT NULL,"
                "label TEXT UNIQUE NOT NULL,"
                "org INTEGER,"
                "FOREIGN KEY(org) REFERENCES organisations(id) )" )

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

        self.dbcon.commit()

        writeTestEntries(self)


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
                match = re.match('\s*(\w*)\s*(?:&\s*(\w*)\s*)?', response)
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
                        label = match.group(1)

                    if match.group(2) == None:
                        org = None
                    else:
                        org = self.getIDfromDict(match.group(2), 'organisations')

        # may FAIL because label not unique!
        if (table == 'people' or table == 'projects') and not org == None:
            self.dbcur.execute(
                "INSERT INTO '%s' (name, label, org) "
                "VALUES(?, ?, ?)" % table, (name, label, org))
        else:
            self.dbcur.execute(
                "INSERT INTO '%s' (name, label) "
                "VALUES(?, ?)" % table, (name, label))

        self.dbcon.commit()

        newid = alog.dbcur.lastrowid

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
            pass
            # print all table entries repeating those in the end that start
            # with the same letters and redo

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
            forid, fortab = self.getIDfromDict(ppo, ('projects', 'people',
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
            act = self.getIDfromDict(match.group(1).lower(), 'activities')
            act = act[0]

            if match.group(2) != None:
                people = self.parsePeople(match.group(2))
            else:
                people = []

            if match.group(3) != None:
                projects, person, orgs = self.parseForinfo(match.group(3))
            else:
                person = []

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
            duration = (enddt - self.lastjob[1]).total_seconds()

            # everything is fine
            if duration >= 0:
                self.dbcur.execute(
                    "UPDATE jobs SET duration=? WHERE id=?", (duration,
                                                              self.lastjob[0]))

                self.dbcon.commit()

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
                            if enddt > self.lastjob[1]:
                                validtime = True
                                self.addDurationToJob(enddt)
                            else:
                                print "New time is still before start of last job!\n"

                        # last: change time of lastjob
                        elif match.group(1).strip() == 'last':
                            # is new time between oldstart and enddt?
                            newdt = dt.datetime.combine(self.lastjob[1].date(),
                                                        dt.time(hours, mins))
                            if oldjob[1] < newdt and newdt < enddt:
                                validtime = True

                                # update lastjob start in DB and self.lastjob
                                self.lastjob = (self.lastjob[0], newdt)
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

        return enddt


    def processJob(self, datetime, jobstr):
        act, people, projects, orgs = self.parseJobStr(jobstr)

        jobid = self.addJobToDB(datetime, act, projects, people, orgs)

        return jobid


    def getTime(self, instr):
        indt = dt.datetime.today()

        if len(instr) == 0:
            jobstr = None
        else:
            match = self.time_re.match(instr)
            jobstr = match.group(1).strip()

            if match.group(2) != None:
                # check whether time is valid
                hours = int(match.group(2))
                mins = int(match.group(3))

                if hours >= 0 and hours < 24 and mins >= 0 and mins < 60:
                    indt = dt.datetime.combine(dt.date.today(),
                                               dt.time(hours, mins))
                else:
                    print "invalid time: taking current time instead\n"

        indt = self.addDurationToJob(indt)

        return indt, jobstr


    # pre-loop for greetings and check for last job without duration
    def preloop(self):
        pass


    # handling of standard activity input
    def default(self, instr):
        indt, jobstr = self.getTime(instr)

        # process job
        lastid = self.processJob(indt, jobstr)
        self.lastjob = (lastid, indt)

        print indt.strftime('%H:%M')


    # delete or overwrite previous jobs
    def do_del(self, instr):
        pass


    # close session
    def do_feierabend(self, instr):
        indt, jobstr = self.getTime(instr)

        return True


if __name__ == "__main__":
    alog = ActivityLog('test.sqlite')
    alog.cmdloop()

#    if alog.dbcon != None:
#        alog.dbcon.close()
