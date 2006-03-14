#!/usr/bin/python

import psycopg,loadable,time

conn=psycopg.connect("dbname=patools16 user=andreaja")
cursor=conn.cursor()


cursor.execute("SELECT MAX(tick) FROM updates")
maxtick = cursor.fetchone()[0]

cursor.execute("SELECT MIN(tick) FROM updates")
mintick =cursor.fetchone()[0]

def hax(start,name,members,size,score,tick):
    taginfo=[]
    intelinfo=[]
    no_tag=[]
    no_intel=[]
    
    query="SELECT t2.id AS id,t1.score AS score,t1.size AS size,t1.id AS pid FROM planet_dump AS t1"
    query+=" INNER JOIN planet_canon AS t2"
    query+=" ON t1.planetname=t2.planetname AND t1.rulername=t2.rulername"
    query+=" INNER JOIN tag AS t3 ON t2.id = t3.pid"
    query+=" INNER JOIN alliance_canon AS t4 ON t4.id = t3.aid"
    query+=" WHERE t1.tick=t3.tick AND t3.tick=%s AND t4.name ILIKE %s"
    cursor.execute(query,(tick-1,name))
    for p in cursor.dictfetchall():
        taginfo.append({'id':p['id'],'pid':p['pid'],'score':p['score'],'size':p['size']})
    #print taginfo

    query="SELECT t2.id AS id,t1.score AS score,t1.size AS size,t1.id AS pid"
    query+=" FROM planet_dump AS t1"
    query+=" INNER JOIN planet_canon AS t2"
    query+=" ON t1.planetname=t2.planetname AND t1.rulername=t2.rulername"
    query+=" INNER JOIN intel AS t3"
    query+=" ON t2.id = t3.pid"
    query+=" INNER JOIN alliance_canon AS t4"
    query+=" ON t4.name ILIKE '%%'||t3.alliance||'%%'"
    query+=" WHERE t1.tick=%s AND t4.name ILIKE %s AND t2.id NOT IN"
    query+=" (SELECT pid FROM tag WHERE aid=t4.id AND tick < t1.tick AND tick > t1.tick-72)"
    cursor.execute(query,(tick,'%'+name+'%'))
    for p in cursor.dictfetchall():    
        intelinfo.append({'id':p['id'],'pid':p['pid'],'score':p['score'],'size':p['size']})
    print intelinfo

    

    #time.sleep(1)
    pass

query="SELECT tick FROM updates WHERE tick=74 ORDER BY tick ASC"

cursor.execute(query)


for t in cursor.dictfetchall():
    query="SELECT name,size,members,score FROM alliance_dump WHERE tick=%s ORDER BY members ASC"
    cursor.execute(query,(t['tick'],))
    start=time.time()
    for a in cursor.dictfetchall():
        if hax(start,a['name'],a['members'],a['size'],a['score'],t['tick']):
            print "Successfully analyzed %s for tick %s" % (a['name'],t['tick'])
        else:
            print "Failed to get info for %s on tick %s" % (a['name'],t['tick'])
        if time.time() > start + 300:
            print "Breaking from tick %s due to excessive time use"
     
"""   
if not alliances.has_key(r['name']):
alliances[r['name']]=[]
if not ticks.has_key(r['tick']):
ticks[r['tick']]=[]
aliances[r['name']].append({'id':r['id'],'name':r['name'],'tick':r['tick'],'members':r['members']})
ticks[r['tick']].append(r['name'])
 
"""
