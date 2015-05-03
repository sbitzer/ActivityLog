# -*- coding: utf-8 -*-
"""
Created on Sun May  3 14:23:25 2015

@author: Sebastian Bitzer (official@sbitzer.eu)
"""

from ActivityLog import ActivityLog
import datetime as dt

def extractjobs(alog, pastdate):
    alog.dbcur.execute(
        "SELECT id, start, duration, activity FROM jobs "
        "WHERE start >= ? "
        "ORDER BY start ASC", (pastdate, ))

    return alog.dbcur.fetchall()


def findlastcommonjob(jobs1, jobs2):
    lcjtime = None
    lcjind = -1
    for j1, j2 in zip(jobs1, jobs2):
        if j1[1] == j2[1]:
            lcjtime = j1[1]
            lcjind = lcjind + 1
        else:
            break

    return lcjind, lcjtime


def getID1fromID2(id2, table, alog1, alog2):
    # check whether activity of job exists in alog1
    if table == 'projects' or table == 'people':
        alog2.dbcur.execute(
            "SELECT name, label, org FROM %s "
            "WHERE id = ?" % table, (id2,))
    else:
        alog2.dbcur.execute(
            "SELECT name, label FROM %s "
            "WHERE id = ?" % table, (id2,))
    nlo = alog2.dbcur.fetchone()

    # if there is an organisation id here, we have to check that, too
    if len(nlo) == 3 and nlo[2] != None:
        orgid = getID1fromID2(nlo[2], 'organisations', alog1, alog2)
        nlo = (nlo[0], nlo[1], orgid)

    alog1.dbcur.execute(
        "SELECT id FROM %s "
        "WHERE name = ?" % table, (nlo[0],))
    id1 = alog1.dbcur.fetchone()

    # if there is no entry with that name in alog1, make one
    if id1 == None:
        if table == 'projects' or table == 'people':
            alog1.dbcur.execute(
                "INSERT INTO %s (name, label, org) "
                "VALUES(?, ?, ?)" % table, nlo)
        else:
            alog1.dbcur.execute(
                "INSERT INTO %s (name, label) "
                "VALUES(?, ?)" % table, nlo)
        id1 = alog1.dbcur.lastrowid
    else:
        id1 = id1[0]

    return id1


if __name__ == "__main__":
    """Merge jobs of two branched activity logs.

    When using the same log across different computers by copying the log
    between computers, because you also want it to be available offline, it can
    happen that two branches of the log are created when the computers cannot
    be properly synced. You will then have two versions of the same log in
    which most jobs match, but there may be jobs in both logs which are not in
    the other log.

    This script merges two branched logs into one. It is assumed that none of
    the non-synced jobs overlap in time. All jobs will be merged in the log
    which has more new jobs. Output will indicate which one that is. If new
    entries need to be created in tables other than 'jobs', then this will be
    done, for example, when a new project was added with one of the new jobs.

    TODO: Also update dictionary (currently not done)."""

    # how many days into the past should you check for deviating jobs?
    pastlim = 14
    pastdate = dt.datetime.today().date() - dt.timedelta(days = pastlim)

    alog1 = ActivityLog('/home/bitzer/work/sebsalog.sqlite')
    alog2 = ActivityLog('/home/bitzer/work/sebsalog_tmp.sqlite')

    jobs1 = extractjobs(alog1, pastdate)
    jobs2 = extractjobs(alog2, pastdate)

    # ensure that alog1 is the one with the most jobs such that you have to do
    # least work when updating alog1
    if len(jobs1) < len(jobs2):
        tmp = jobs1
        jobs1 = jobs2
        jobs2 = tmp

        tmp = alog1
        alog1 = alog2
        alog2 = tmp

    lcjind, lcjtime = findlastcommonjob(jobs1, jobs2)

    tabnames = [['job_pj', 'project', 'projects'],
                ['job_p', 'person', 'people'],
                ['job_org', 'org', 'organisations']]

    # insert jobs from alog2, which are missing in alog1, into alog1
    for job in jobs2[lcjind+1:]:
        # get alog1-id of activity for job
        actid = getID1fromID2(job[3], 'activities', alog1, alog2)

        # [optional] check whether times of job overlap with existing ones in alog1

        # add job to alog1
        alog1.dbcur.execute(
            "INSERT INTO jobs (start, duration, activity) "
            "VALUES (?, ?, ?)", (job[1], job[2], actid))
        jobid = alog1.dbcur.lastrowid

        # for projects, people and organisations:
        for tnames in tabnames:
            # get all items associated with this job
            alog2.dbcur.execute(
                "SELECT %s FROM %s "
                "WHERE job = ?" % (tnames[1], tnames[0]), (job[0],))
            rows2 = alog2.dbcur.fetchall()

            # record those items in alog1
            for id2 in rows2:
                id1 = getID1fromID2(id2[0], tnames[2], alog1, alog2)

                alog1.dbcur.execute(
                    "INSERT INTO %s (job, %s) "
                    "VALUES (?, ?)" % (tnames[0], tnames[1]), (jobid, id1))

    alog1.dbcon.commit()

    print "merged %d jobs into: %s" % (len(jobs2)-lcjind-1, alog1.dbname)