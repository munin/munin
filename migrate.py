#!/usr/bin/python

import psycopg, sys

user="andreaja"

try:
    old_db=sys.argv[1]
    new_db=sys.argv[2]
except:
    print "Usage: %s <old_db> <new_db>" % (sys.argv[0])
    sys.exit(0)


old_conn=psycopg.connect("user=%s dbname=%s" %(user,old_db))
new_conn=psycopg.connect("user=%s dbname=%s" %(user,new_db))

old_curs=old_conn.cursor()

new_curs=new_conn.cursor()

old_curs.execute("SELECT t1.pnick AS pnick,t1.userlevel AS userlevel FROM user_list AS t1 WHERE t1.stay")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO user_list (pnick,userlevel) VALUES (%s,%s)",(u['pnick'],u['userlevel']))

new_conn.commit()
