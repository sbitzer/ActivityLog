#!/usr/bin/env ipython
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 21:01:20 2015

@author: Sebastian Bitzer (official@sbitzer.eu)
"""

from ActivityLog import ActivityLog

with ActivityLog('test.sqlite') as alog:
    alog.cmdloop()

