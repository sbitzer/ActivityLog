# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 21:41:18 2015

@author: Zibbi
"""
from ActivityLog import ActivityLog
import csv
import datetime
import pickle
import sys
import traceback

def convMatlabdate2Datetime(matdate):
    # Matlab's and Python's definition of the ordinal date format differ
    # by 1 year and 1 day
    dt = datetime.datetime.fromordinal(int(matdate) - 366)
    H = matdate % 1 * 24
    M = H % 1 * 60
    S = M % 1 * 60

    dt = dt.replace(hour=int(H), minute=int(M), second=int(S))

    return dt


if __name__ == "__main__":
    alog = ActivityLog('sebsalog.sqlite')

    # endt may change when faulty input is corrected during computation of durations
    endt_ischanged = False
    endt_new = datetime.datetime.now()

    try:
        fi = open('lastrowinfo.pkl','r')
    except IOError:
        initrow = 1
    else:
        lastrowinfo = pickle.load(fi)
        initrow = lastrowinfo[0]
        fi.close()

    if initrow > 1:
        print "Resuming with row %d!" % initrow
        print "---------------------"

    # loop over entries in the csv file
    with open('activitylog_tmp.csv', 'rb') as alogfile:
        reader = csv.reader(alogfile, delimiter=';', skipinitialspace=True)
        count = 0
        for row in reader:
            count = count + 1

            if count < initrow:
                continue

            # extract datetimes for job
            if endt_ischanged:
                startt = endt_new
            else:
                startt = convMatlabdate2Datetime(float(row[0]))
            endt = convMatlabdate2Datetime(float(row[1]))

            # if you resume a previous run
            if count == initrow & count > 1:
                # check that start time of this job and end time of stored last
                # job match
                if startt == lastrowinfo[3]:
                    # set lastjob to that stored in lastrowinfo
                    alog.lastjob = (lastrowinfo[1], lastrowinfo[2])
                else:
                    print "Start time of the job to resume and end time"
                    print "of stored previous job do not match."
                    print "Something wrong. Shutting down."
                    break

            print startt, row[2]

            # separate out jobstr from time string
            jobstr = alog.time_re.match(row[2]).group(1).strip()

            try:
                # add job to DB
                jobid = alog.processJob(startt, jobstr)
            except:
                print "Error in row %d when adding job." % count
                print "row info:"
                print row
                print "error info:"
                traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
                print "Shutting down."

                fi = open('lastrowinfo.pkl','w')
                pickle.dump([count, alog.lastjob[0], alog.lastjob[1], startt], fi)
                fi.close()

                break
            else:
                # update lastjob
                alog.lastjob = (jobid, startt)

                try:
                    # add duration
                    endt_new = alog.addDurationToJob(endt)
                except:
                    print "Error in row %d when adding duration." % count
                    print "row info:"
                    print row
                    print "error info:"
                    traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
                    print "Add duration manually, update endt in lastrowinfo, " \
                        "if necessary, then resume!"
                    print "Shutting down."

                    fi = open('lastrowinfo.pkl','w')
                    pickle.dump([count+1, jobid, startt, endt], fi)
                    fi.close()

                    break
                else:
                    endt_ischanged = endt_new != endt
