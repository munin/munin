#!/usr/bin/python

import sys
import time

import os
from psycopg2 import psycopg1 as psycopg
import traceback

sys.path.insert(0, "custom")

import scan

t_start = time.time()
t1 = t_start

ofile = file("pid.sleipnir", "w")
ofile.write("%s" % (os.getpid(),))
ofile.close()

conn = psycopg.connect("dbname=patools27 user=munin")
conn.serialize()
conn.autocommit()


cursor = conn.cursor()


query = "SELECT rand_id FROM scanparser_queue"

cursor.execute(query)
result = cursor.dictfetchall()
for r in result:
    rid = str(r["rand_id"])
    query = "SELECT rand_id FROM scan WHERE"
    #    query+=" tick > (SELECT max_tick()) - 72"
    query += " rand_id = %s"
    cursor.execute(query, (rid,))

    if cursor.rowcount > 0:
        query = "DELETE FROM scanparser_queue WHERE rand_id = %s"
        cursor.execute(query, (rid,))
        print "Already have scan %s" % (r["rand_id"],)
        continue

    print "Fetching scan %s" % (rid,)
    while True:
        try:
            s = scan.scan(rid, None, conn, cursor, "webinterface", "webinterface", None)
            break
        except Exception, e:
            print "failed"
            time.sleep(0.5)
            continue
    # s.run()
    try:
        s.unsafe_method()
    except Exception, e:
        print "Exception in scan: " + e.__str__()
        traceback.print_exc()
        continue

    query = "DELETE FROM scanparser_queue WHERE rand_id = %s"
    cursor.execute(query, (rid,))

    time.sleep(0.4)
conn.commit()
