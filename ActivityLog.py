# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 19:07:49 2014

@author: Sebastian Bitzer
"""

import sqlite3

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
        "INSERT INTO activities (act_name, act_label) VALUES('email', 'email')")
    alog.dbcur.execute(
        "INSERT INTO activities (act_name, act_label) VALUES('break', 'break')")
    alog.dbcur.execute(
        "INSERT INTO activities (act_name, act_label) VALUES('lunch', 'lunch')")
    alog.dbcur.execute(
        "INSERT INTO projects (pj_name, pj_label) VALUES('BeeExp', 'BeeExp')")
    alog.dbcur.execute(
        "INSERT INTO projects (pj_name, pj_label) VALUES('Bayesian attractor model', 'BAttM')")
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

    def __init__(self, dbname):
        dbstate = isSQLite3(dbname)
        if dbstate == 1:
            self.dbcon = sqlite3.connect(dbname)
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


    def initDB(self):
        """Creates a database with the predefined schema."""

        self.dbcur.execute(
            "CREATE TABLE activities ("
                "act_id INTEGER PRIMARY KEY,"
                "act_name TEXT NOT NULL,"
                "act_label TEXT UNIQUE NOT NULL )" )

        self.dbcur.execute(
            "CREATE TABLE organisations ("
                "org_id INTEGER PRIMARY KEY,"
                "org_name TEXT NOT NULL,"
                "org_label TEXT UNIQUE NOT NULL )" )

        self.dbcur.execute(
            "CREATE TABLE people ("
                "p_id INTEGER PRIMARY KEY,"
                "p_name TEXT NOT NULL,"
                "p_label TEXT UNIQUE NOT NULL,"
                "p_org INTEGER,"
                "FOREIGN KEY(p_org) REFERENCES organisations(org_id) )" )

        self.dbcur.execute(
            "CREATE TABLE projects ("
                "pj_id INTEGER PRIMARY KEY,"
                "pj_name TEXT NOT NULL,"
                "pj_label TEXT UNIQUE NOT NULL,"
                "pj_org INTEGER,"
                "FOREIGN KEY(pj_org) REFERENCES organisations(org_id) )" )

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
                "job_id INTEGER PRIMARY KEY,"
                "start TEXT NOT NULL UNIQUE,"
                "end TEXT NOT NULL UNIQUE,"
                "activity INTEGER NOT NULL,"
                "FOREIGN KEY(activity) REFERENCES activities(act_id) )" )

        # the following tables implement possible one-to-many relationships
        # between jobs and people, projects and organisations

        self.dbcur.execute(
            "CREATE TABLE job_p ("
                "job INTEGER,"
                "person INTEGER,"
                "PRIMARY KEY(job, person),"
                "FOREIGN KEY(job) REFERENCES jobs(job_id),"
                "FOREIGN KEY(person) REFERENCES people(p_id) )" )

        self.dbcur.execute(
            "CREATE TABLE job_pj ("
                "job INTEGER,"
                "project INTEGER,"
                "PRIMARY KEY(job, project),"
                "FOREIGN KEY(job) REFERENCES jobs(job_id),"
                "FOREIGN KEY(project) REFERENCES projects(pj_id) )" )

        self.dbcur.execute(
            "CREATE TABLE job_org ("
                "job INTEGER,"
                "org INTEGER,"
                "PRIMARY KEY(job, org),"
                "FOREIGN KEY(job) REFERENCES jobs(job_id),"
                "FOREIGN KEY(org) REFERENCES organisations(org_id) )" )

        self.dbcon.commit()

        writeTestEntries(self)


    def parseJobStr(self, jobstr):
        """parses the raw input from the user"""
        pass

        # act
        # act with {people}
        # act with {people} for project
        # act for project
        # act for org
        # act for person

    def getIDfromDict(self, name, table):
        self.dbcur.execute(
            "SELECT tab_name, tab_id FROM dictionary WHERE word = ?", (name, ) )
        result = self.dbcur.fetchone()
        if result == None:
            # name is not in dictionary:
            return None
        else:
            assert( result[0] == table )
            return result[1]


    def addEntry(self, start, end, act_id, proj=None, people=None, org=None):
        # get or add activity ID
        pass


        # get or add project IDs

        # get or add people IDs

        # get or add organisation IDs

if __name__ == "__main__":
    alog = ActivityLog('test.sqlite')

#    if alog.dbcon != None:
#        alog.dbcon.close()
