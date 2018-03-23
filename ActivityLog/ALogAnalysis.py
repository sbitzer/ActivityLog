#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 28 15:17:43 2018

@author: bitzer
"""

import datetime as dt
import pandas as pd

class ALogAnalysis(object):
    """Provides analysis routines for an activity log."""

    def __init__(self, alog):
        self.alog = alog

    def sum_durations(self, start, end=None, exclude_acts='lunch',
                      longbreaklimit=10):
        """Returns sum of durations in minutes within a given time window.

        Excludes all jobs with activities listed in exclude_acts and all jobs
        with activity 'break' and duration longer than longbreaklimit.
        """

        if end is None:
            end = dt.datetime.today()
        elif not isinstance(end, (dt.date, dt.datetime)):
            raise TypeError("The end argument has to be a date or datetime.")

        if start == 'day':
            start = dt.datetime.today().date()
        elif start == 'week':
            today = dt.datetime.today().date()
            start = today - dt.timedelta(today.weekday())
        elif not isinstance(start, (dt.date, dt.datetime)):
            raise TypeError("The start argument has to be a date or datetime.")

        if isinstance(exclude_acts, basestring):
            exclude_acts = (exclude_acts, )
        elif isinstance(exclude_acts, list):
            exclude_acts = tuple(exclude_acts)
        elif not isinstance(exclude_acts, tuple):
            raise TypeError("exclude_acts should either be string, list, or "
                            "tuple!")

        # working hours for today:
        # sum the duration of jobs, but exclude lunches and breaks > 10min
        self.alog.dbcur.execute(
            "SELECT SUM(duration) FROM jobs "
            "WHERE start >= ? AND start <= ? "
            "AND NOT activity IN ("
                "SELECT id FROM activities "
                "WHERE name IN (%s) ) "
            "AND NOT ( "
                "activity IN ("
                    "SELECT id FROM activities "
                    "WHERE name IN ('break') ) "
                "AND duration > ? )" % ', '.join('?' for a in exclude_acts),
            (start, end) + exclude_acts + (float(longbreaklimit) * 60, ))
        total_dur = self.alog.dbcur.fetchone()[0]

        if total_dur is None:
            total_dur = 0
        else:
            total_dur = total_dur / 60

        return total_dur

    def get_weekly_project_durations(self, week=0):
        """Returns the durations spent on different projects in selected week.

        Counts people as projects unless the job having people associated with
        it also is associated with an explicit project (example: "meeting with
        Alex and Deborah for project2".

        Also returns for each of the projects durations spent in each activity
        that occurred at least once in that week.

        The durations may sum to a value larger than the total duration spent
        in jobs in that week, because an individual job may be associated with
        several projects and then occurs multiple times in the job list for
        this week.
        """

        # get the start and end of the desired week
        now = dt.datetime.now()
        monday = now.date() - dt.timedelta(days=now.weekday() + 7*week)
        nextmonday = monday + dt.timedelta(days=7)

        # get all jobs and associated projects for the selected week
        # there will be one row per job and associated project such that a job
        # which is assigned to two projects will also have two rows
        self.alog.dbcur.execute(
            'WITH ja (id, start, dur, act) AS ('
            '    SELECT jobs.id, jobs.start, jobs.duration, activities.label '
            '    FROM jobs JOIN activities ON jobs.activity = activities.id '
            '    WHERE jobs.start >= ? AND jobs.start < ?) '
            'SELECT ja.id, ja.start, ja.dur, ja.act, projects.label '
            'FROM ja LEFT OUTER JOIN job_pj ON ja.id = job_pj.job '
            '    LEFT OUTER JOIN projects ON job_pj.project = projects.id',
            (monday, nextmonday))

        jobs = pd.DataFrame(self.alog.dbcur.fetchall(),
                            columns=('id', 'start', 'duration', 'act',
                                     'project'))

        # do the same thing for people, but do not select jobs here that have a
        # project associated with them
        # note that it's not necessary to outer join here, because I have already
        # got all the necessary information about jobs above
        self.alog.dbcur.execute(
            'SELECT jobs.id, people.label '
            'FROM jobs JOIN job_p, people '
            '    ON jobs.id = job_p.job AND job_p.person = people.id '
            'WHERE jobs.start >= ? '
            '    AND jobs.start < ?'
            '    AND jobs.id NOT IN (SELECT job FROM job_pj)',
            (monday, nextmonday))

        j_p = pd.DataFrame(self.alog.dbcur.fetchall(),
                           columns=('id', 'person'))

        # sort the people as projects into the job list
        ids = j_p.id.unique()
        for jid in ids:
            people = j_p[j_p.id == jid].person

            row = jobs[jobs.id == jid].copy()
            row.project = people.iloc[0]

            # add first person to the corresponding job
            jobs[jobs.id == jid] = row

            # if several people are associated with the job, add more rows to the
            # job list
            for person in people.values[1:]:
                row.project = person
                jobs = jobs.append(row, ignore_index=True)

        projects = pd.DataFrame(jobs.groupby('project').duration.sum(
                ).sort_values(ascending=False))
        acts = jobs.act.unique()

        for act in acts:
            projects[act] = 0

        for pj in projects.index:
            actdurs = jobs[jobs.project == pj].groupby('act').duration.sum()

            projects.loc[pj, actdurs.index] = actdurs

        # remove activities which did not occur in any of the projects
        # (these are project-independent activities)
        projects = projects.T[projects.sum() > 0].T

        return projects