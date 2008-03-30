import psycopg,time

t_start=time.time()
t1=t_start

conn=psycopg.connect("dbname=patools19 user=andreaja")
conn.serialize()
conn.autocommit()
                
cursor=conn.cursor()

cursor.execute("SELECT tick FROM updates")

for t in range(1297,1317):
    tick=t

    t2=time.time()-t_start
    print "Tick: %d (%.3fs so far)" % (tick,t2)
    t1=time.time()

    query = """
    UPDATE planet_dump SET vdiff = t1.value - t2.value
    FROM planet_dump AS t1
    INNER JOIN planet_dump AS t2
    ON t1.id=t2.id AND t1.tick-1=t2.tick AND t1.tick = %s
    WHERE planet_dump.tick = %s AND planet_dump.id=t1.id;
    """
    
    cursor.execute(query,(tick,tick))

    t2=time.time()-t1
    print "vdiffs in %.3fs" % (t2,)
    t1=time.time()

    query = """
    UPDATE planet_dump SET idle = t2.idle+1
    FROM planet_dump AS t2
    WHERE planet_dump.id = t2.id AND planet_dump.tick = %s AND planet_dump.tick - 1 = t2.tick
    AND planet_dump.vdiff >= t2.vdiff - 1 AND planet_dump.vdiff <= t2.vdiff + 1 AND planet_dump.xp - t2.xp = 0
    """

    cursor.execute(query,(tick,))

    t2=time.time()-t1
    print "idle count in %.3fs" % (t2,)
    t1=time.time()
    
