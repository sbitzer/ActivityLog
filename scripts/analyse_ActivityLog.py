# this is an example of a join statement over three tables:
SELECT jobs.start, activities.name, job_pj.project FROM jobs JOIN activities, job_pj ON jobs.activity = activities.id AND jobs.id = job_pj.job WHERE jobs.start >= "2014-07-01" AND jobs.start < "2014-08-09" AND job_pj.project == 37
