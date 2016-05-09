# -*- coding: utf-8 -*-
"""
Created on Sun May  8 14:57:34 2016

@author: Sebastian Bitzer (official@sbitzer.eu)
"""

# this is an example of a join statement over three tables:
# SELECT jobs.start, activities.name, job_pj.project FROM jobs JOIN activities, job_pj ON jobs.activity = activities.id AND jobs.id = job_pj.job WHERE jobs.start >= "2014-07-01" AND jobs.start < "2014-08-09" AND job_pj.project == 37

import datetime as dt
from ActivityLog import ActivityLog

def show_lastweek(alog):
    """shows the proportion of times spent on the different projects last week"""

    # get current date
    now = dt.datetime.now()

    # get all jobs and associated projects for last week


    print('nothing done')

with ActivityLog("test.sqlite") as alog:
    show_lastweek(alog)