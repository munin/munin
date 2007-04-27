#!/usr/bin/python 

import psycopg,time,urllib2,sys,os,re

from loadable import planet
from loadable import galaxy
from loadable import alliance

import scan

t_start=time.time()
t1=t_start

ofile=file("pid.sleipnir", "w")
ofile.write("%s" % (os.getpid(),))
ofile.close()

conn=psycopg.connect("dbname=patools21 user=munin")
cursor=conn.cursor()

query="SELECT rand_id FROM scanparser_queue"

result=cursor.execute(query)

for r in result:
    query="SELECT rand_id FROM scan WHERE"
    query+=" tick > (SELECT max_tick()) - 48"
    query+=" AND rand_id = %s"
    res=cursor.execute(query,(r['rand_id'],))
    if cursor.rowcount > 0:
        continue

    scan.scan(r['rand_id'],None,conn,cursor,'webinterface','webinterface')
