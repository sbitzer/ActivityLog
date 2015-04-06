#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 21:01:20 2015

@author: Sebastian Bitzer (official@sbitzer.eu)
"""

from ActivityLog import ActivityLog

alog = ActivityLog('sebsalog.sqlite')
alog.cmdloop()

if alog.dbcon != None:
    alog.dbcon.close()