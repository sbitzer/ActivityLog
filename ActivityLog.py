# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 19:07:49 2014

@author: Sebastian Bitzer
"""

import sqlite3
import re
import itertools
import datetime as dt


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

    alog.dbcon.commit()


class ActivityLog(object):
    """A class which defines and manipulates an activity log"""

    # this separates the three parts of a job string:
    # activity[ with people][ for project|org|person]
    act_re = re.compile('([\w ]+?)(?: with ([\w ,]+?))?(?:$| for ([\w ,]+))')

    lastjob = ('', dt.datetime.min)

    def __init__(self, dbname):
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
                self.dbcon = sqlite3.connect(dbname)
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
                "end TIMESTAMP NOT NULL UNIQUE,"
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
            response = raw_input("You can now provide a shorter version of %s as "
                "label, \nif you wish. If you currently add a person or project\n"
                "to the database, you may assign that to an organisation.\n"
                "Provide this as 'label § organisation'! You can leave\n"
                "anyone of them empty as long as you provide the '§'.\n"
                "Simply press ENTER to use %s as label and no organisation:\n"
                % (name, name))
            if response == '':
                corrinput = True
                label = name
                org = None
            else:
                match = re.match('(\w*)\s*§\s*(\w*)', response)
                if match == None:
                    print("DID NOT RECOGNISE FORMAT!\n"
                          "Make sure you follow the instructions below!\n"
                          "Only use alpha-numeric names on either side of the §!\n\n")
                    continue
                else:
                    corrinput = True

                    if match.group(1) == '':
                        label = name
                    else:
                        label = match.group(1)

                    if match.group(2) == '':
                        org = None
                    else:
                        org = self.getIDfromDict(match.group(2), 'organisations')

        try:
            if (table == 'people' or table == 'projects') and not org == None:
                self.dbcur.execute(
                    "INSERT INTO ? (name, label) "
                    "VALUES(?, ?)", (table, name, label))
            else:
                self.dbcur.execute(
                    "INSERT INTO ? (name, label, org) "
                    "VALUES(?, ?, ?)", (table, name, label, org))

            self.dbcon.commit()

            newid = alog.dbcur.lastrowid
        # TODO: specify proper exception to catch
        except:
            print("Database insertion failed: skipping\n")
            newid = None

        return newid


    def resolveUnknownName(self, name, table):
        if len(table) > 1:
            tabstr = '0: %s' % table[0]
            for i, tab in enumerate(table[1:]):
                tabstr = tabstr + ', %d: %s' % (i+1, tab)

            response = raw_input("I'm sorry. Does %s belong into %s?:\n" % (name, tabstr))
            table = table[int(response)]
        else:
            table = table[0]

        # misspelled, new alias, or new entry?
        response = raw_input("There is no %s in %s. Add in %s (1), "
            "add as alias (2: name) or check DB (3)?\n"
            "If you made a typo, you can also just provide the name again "
            "without the typo:\n" % (name, table, table))

        if response[0] == '1':
            return (self.addBaseType(name, table), table)
        elif response[0] == '2':
            nameintab = response[2:]
            tab_id = self.getIDfromDict(nameintab, table)
            self.dbcur.execute(
                "INSERT INTO dictionary (word, tab_name, tab_id) "
                "VALUES(?, ?, ?)", (name, table, tab_id))
            self.dbcon.commit()

            return (tab_id, table)
        elif response[0] == '3':
            pass
            # print all table entries repeating those in the end that start
            # with the same letters and redo

        else:
            return self.getIDfromDict(response, table)


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
            "WHERE word = ? and tab_name IN %s" % placeholders, (name,)+ table )
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

        # project-organisation list
        polist = map( lambda s: s.split(', '), forstr.split(' and ') )
        polist = list( itertools.chain.from_iterable(polist) )

        pjids = []
        orgids = []
        for po in polist:
            forid, fortab = self.getIDfromDict(po, ('projects', 'organisations'))

            if fortab == 'projects':
                pjids.append(forid)
            else:
                orgids.append(forid)

        if len(pjids) == 0:
            pjids = None
        if len(orgids) == 0:
            orgids = None

        return pjids, orgids


    def parseJobStr(self, jobstr):
        """parses the raw input from the user"""

        # act
        # act with {people}
        # act with {people} for project
        # act for project
        # act for org
        # act for person

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

            if match.group(3) != None:
                projects, orgs = self.parseForinfo(match.group(3))

        return act, people, projects, orgs


    def addJobToDB(self, start, end, act, projects=None, people=None, orgs=None):
        # add job to jobs table and retrieve its id
        self.dbcur.execute(
            "INSERT INTO jobs (start, end, activity) "
            "VALUES(?, ?, ?)", (start, end, act) )
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


    def processJob(self, date, jobstr):
        act, people, projects, orgs = self.parseJobStr(jobstr)




if __name__ == "__main__":
    alog = ActivityLog('test.sqlite')

#    if alog.dbcon != None:
#        alog.dbcon.close()
