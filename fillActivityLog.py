# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 21:41:18 2015

@author: Zibbi
"""
from ActivityLog import ActivityLog

if __name__ == "__main__":
    alog = ActivityLog('test.sqlite')

    # loop over entries in the csv file
    # extract datetime for job
    # use a function which takes jstr and datetime to add job