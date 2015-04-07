#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 21:01:20 2015

@author: Sebastian Bitzer (official@sbitzer.eu)
"""

import sys

sys.path.append('/home/bitzer/Projekte/activitylog')

from ActivityLog import ActivityLog

alog = ActivityLog('/home/bitzer/Projekte/activitylog/sebsalog.sqlite')
alog.cmdloop()

if alog.dbcon != None:
    alog.dbcon.close()

raw_input('Press enter to close ...')
