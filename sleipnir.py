#!/usr/bin/python 

import psycopg,time,urllib2,sys,os,re

from loadable import planet
from loadable import galaxy
from loadable import alliance

t_start=time.time()
t1=t_start

ofile=file("pid.sleipnir", "w")
ofile.write("%s" % (os.getpid(),))
ofile.close()

conn=psycopg.connect("dbname=patools21 user=munin")
cursor=conn.cursor()

 
