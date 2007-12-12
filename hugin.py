#!/usr/bin/python

# This file is part of Munin.

# Munin is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# Munin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Munin; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen 
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright 
# owners.

import psycopg,time,urllib2,sys,os,re,traceback

from loadable import planet
from loadable import galaxy
from loadable import alliance

t_start=time.time()
t1=t_start

ofile=file("pid.hugin", "w")
ofile.write("%s" % (os.getpid(),))
ofile.close()

while True:
    try:
        conn=psycopg.connect("dbname=patools24 user=munin")
        cursor=conn.cursor()

        cursor.execute("SELECT MAX(tick) FROM updates")
        last_tick=int(cursor.fetchone()[0])
        if not last_tick:
            last_tick = -1

        try:
            planets = urllib2.urlopen("http://game.planetarion.com/botfiles/planet_listing.txt")
        except Exception, e:
            print "Failed gathering planet listing."
            print e.__str__()
            time.sleep(300)
            continue
        try:
            galaxies = urllib2.urlopen("http://game.planetarion.com/botfiles/galaxy_listing.txt")
        except Exception, e:
            print "Failed gathering galaxy listing."
            print e.__str__()
            time.sleep(300)
            continue    
        try:
            alliances = urllib2.urlopen("http://game.planetarion.com/botfiles/alliance_listing.txt")
        except Exception, e:
            print "Failed gathering alliance listing."
            print e.__str__()
            time.sleep(300)
            continue

        planets.readline();planets.readline();planets.readline();
        tick=planets.readline()
        m=re.search(r"tick:\s+(\d+)",tick,re.I)
        if not m:
            print "Invalid tick: '%s'" % (tick,)
            time.sleep(120)
            continue
        planet_tick=int(m.group(1))
        print "Planet dump for tick %s" % (planet_tick,)
        planets.readline();planets.readline();planets.readline();

        galaxies.readline();galaxies.readline();galaxies.readline();
        tick=galaxies.readline()
        m=re.search(r"tick:\s+(\d+)",tick,re.I)
        if not m:
            print "Invalid tick: '%s'" % (tick,)
            time.sleep(120)
            continue
        galaxy_tick=int(m.group(1))
        print "Galaxy dump for tick %s" % (galaxy_tick,)
        galaxies.readline();galaxies.readline();galaxies.readline();

        alliances.readline();alliances.readline();alliances.readline();
        ptick=alliances.readline()
        m=re.search(r"tick:\s+(\d+)",tick,re.I)
        if not m:
            print "Invalid tick: '%s'" % (tick,)
            time.sleep(120)
            continue
        alliance_tick=int(m.group(1))
        print "Alliance dump for tick %s" % (alliance_tick,)
        alliances.readline();alliances.readline();alliances.readline();

        if not (planet_tick == galaxy_tick  == alliance_tick):
            print "Varying ticks found, sleeping"
            print "Planet: %s, Galaxy: %s, Alliance: %s" % (planet_tick,galaxy_tick,alliance_tick)
            time.sleep(30)
            continue
        if not planet_tick > last_tick:
            print "Stale ticks found, sleeping"            
            time.sleep(60)
            continue

        t2=time.time()-t1
        print "Loaded dumps from webserver in %.3f seconds" % (t2,)
        t1=time.time()

        ptmp='ptmp'
        gtmp='gtmp'
        atmp='atmp'

        query="""
        CREATE TEMP TABLE %s (
         x smallint,
         y smallint,
         z smallint,
         planetname varchar(22) NOT NULL,
         rulername varchar(22) NOT NULL,
         race char(3) CHECK (race in (NULL,'Ter','Cat','Xan','Zik','Etd')),
         size smallint NOT NULL,
         score integer NOT NULL,
         value integer NOT NULL,
         xp integer NOT NULL
         )
        """ % (ptmp,)
        cursor.execute(query)
        cursor.copy_from(planets,ptmp,"\t")

        query="""
        CREATE TEMP TABLE %s (
         x smallint,
         y smallint,
         name varchar(66) NOT NULL,
         size int NOT NULL,
         score bigint NOT NULL,
         value bigint NOT NULL,
         xp integer NOT NULL
        )
        """ % (gtmp,)
        cursor.execute(query)
        cursor.copy_from(galaxies,gtmp,"\t")

        query="""
        CREATE TEMP TABLE %s (
         score_rank smallint NOT NULL,
         name varchar(18) NOT NULL,
         size int NOT NULL,
         members smallint NOT NULL,
         score bigint NOT NULL
        )
        """ % (atmp,)
        cursor.execute(query)
        cursor.copy_from(alliances,atmp,"\t")    

        t2=time.time()-t1
        print "Copied dumps in %.3f seconds" % (t2,)
        t1=time.time()

        query="SELECT store_update(%d::smallint,%s,%s,%s)"
        cursor.execute(query,(planet_tick,ptmp,gtmp,atmp))

        query="SELECT store_planets(%d::smallint)"
        cursor.execute(query,(planet_tick,))
        t2=time.time()-t1
        print "Processed and inserted planet dumps in %.3f seconds" % (t2,)
        t1=time.time()    


        #query="SELECT * FROM %s" % (ptmp,)
        #cursor.execute(query)
        #for result in cursor.dictfetchall():
        #    print result

        query="SELECT store_galaxies(%d::smallint)"
        cursor.execute(query,(galaxy_tick,))
        t2=time.time()-t1
        print "Processed and inserted galaxy dumps in %.3f seconds" % (t2,)
        t1=time.time()

        query="SELECT store_alliances(%d::smallint)"
        cursor.execute(query,(alliance_tick,))    
        t2=time.time()-t1
        print "Processed and inserted alliance dumps in %.3f seconds" % (t2,)
        t1=time.time()    

        conn.commit()
        break
    except Exception, e:
        print "Something random went wrong, sleeping for 15 seconds to hope it improves"
        print e.__str__()
        traceback.print_exc()
        time.sleep(15)
        continue


t2=time.time()-t1
t1=time.time()-t_start
print "Commit in %.3f seconds" % (t2,)
print "Total time taken: %.3f seconds" % (t1,)

"""
#    query ="INSERT INTO planet_temp "
#    query+="(tick,x,y,z,planetname,rulername,race,size,score,value,xp) "
#    query+="VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
#    for line in planets[7:]:
#        p=line.strip().split("\t")
#        print "inserting: %s"% p,
#        cursor.execute(query,(planet_tick,p[0],p[1],p[2],p[3].strip("\""),p[4].strip("\""),p[5],p[6],p[7],p[8],p[9]))
#        if cursor.rowcount < 1:
#            raise

#    query="COPY planet_temp (x,y,z,planetname,rulername,race,size,score,value,xp) FROM STDIN WITH DELIMITER '\t'"



    #for result in cursor.dictfetchall():
    #    print result
    
    #query="SELECT * FROM planet_temp"
    #cursor.execute(query)


    #planets[7:]:
    



     score_rank smallint ,
     value_rank smallint ,
     size_rank smallint ,
     xp_rank smallint ,
     tick smallint,
     id integer 

    p_list=[]
    g_list=[]
    a_list=[]
    
    for line in planets[7:]:
        p=line.strip().split("\t")
        tmp_plan=planet(p[0],p[1],p[2],p[3].strip("\""),p[4].strip("\""),p[5],p[6],p[7],p[8])
        tmp_plan.xp=(int(tmp_plan.score)-int(tmp_plan.value))/60
        p_list.append(tmp_plan)
        
    for line in galaxies[7:]:
        g=line.strip().split("\t")
        tmp_gal=galaxy(g[0],g[1],g[2].strip("\""),g[3],g[4],g[5])
        tmp_gal.xp=(int(tmp_gal.score)-int(tmp_gal.value))/60
        g_list.append(tmp_gal)

    for line in alliances[7:]:
        a=line.strip().split("\t")
        tmp_all=alliance(a[0],a[1].strip("\""),a[2],a[3],a[4])
        a_list.append(tmp_all)    


    p_list.sort(cmp_score_asc)
    for i in range(len(p_list)):
        p_list[i].score_rank=i+1

    p_list.sort(cmp_value_asc)
    for i in range(len(p_list)):
        p_list[i].value_rank=i+1

    p_list.sort(cmp_xp_asc)
    for i in range(len(p_list)):
        p_list[i].xp_rank=i+1

    p_list.sort(cmp_size_asc)
    for i in range(len(p_list)):
        p_list[i].size_rank=i+1        

    g_list.sort(cmp_score_asc)
    for i in range(len(g_list)):
        g_list[i].score_rank=i+1

    g_list.sort(cmp_value_asc)
    for i in range(len(g_list)):
        g_list[i].value_rank=i+1

    g_list.sort(cmp_xp_asc)
    for i in range(len(g_list)):
        g_list[i].xp_rank=i+1

    g_list.sort(cmp_size_asc)
    for i in range(len(g_list)):
        g_list[i].size_rank=i+1

    a_list.sort(cmp_score_asc)
    for i in range(len(a_list)):
        a_list[i].score_rank=i+1
    a_list.sort(cmp_members_asc)
    for i in range(len(a_list)):
        a_list[i].members_rank=i+1
    a_list.sort(cmp_size_asc)
    for i in range(len(a_list)):
        a_list[i].size_rank=i+1        

    t2=time.time()-t1
    print "Generated ranks in %.3f seconds" % (t2,)
    t1=time.time()

    p_canon=[]
    g_canon=[]
    a_canon=[]

    p_new=[]
    g_new=[]    
    a_new=[]

    query="SELECT id,planetname,rulername,active FROM planet_canon"
    cursor.execute(query)
    for result in cursor.dictfetchall():
        p_canon.append(result)
    query="SELECT id,x,y,active FROM galaxy_canon"
    cursor.execute(query)
    for result in cursor.dictfetchall():
        g_canon.append(result)        
    query="SELECT id,name,active FROM alliance_canon"
    cursor.execute(query)
    for result in cursor.dictfetchall():
        a_canon.append(result)

    t2=time.time()-t1
    print "Fetched canonical in %.3f seconds" % (t2,)
    t1=time.time()
            
    for p in p_list:
        for p_can in p_canon:
            if p.planetname == p_can['planetname'] and p.rulername == p_can['rulername']:
                p.id=p_can['id']
                p_can['found']=True
                break
        if p.id == -1:
            p_new.append(p)

    for g in g_list:
        for g_can in g_canon:
            if g.x == g_can['x'] and g.y == g_can['y']:
                g.id=g_can['id']
                g_can['found']=True
                break
        if g.id == -1:
            g_new.append(g)

    for a in a_list:
        for a_can in a_canon:
            if a.name == a_can['name']:
                a.id=a_can['id']
                a_can['found']=True
                break
        if a.id == -1:
            a_new.append(a)

    t2=time.time()-t1
    print "Checked intersection with canonical in %.3f seconds" % (t2,)
    t1=time.time()

    query="UPDATE planet_canon SET active = FALSE WHERE planetname = %s AND rulername = %s"
    for p in p_canon:
        if not p.has_key('found'):
            cursor.execute(query,(p['planetname'],p['rulername']))
            if cursor.rowcount < 1:
                raise

    query="UPDATE galaxy_canon SET active = FALSE WHERE x = %s AND y = %s"
    for g in g_canon:
        if not g.has_key('found'):
            cursor.execute(query,(g['x'],g['y']))
            if cursor.rowcount < 1:
                raise            

    query="UPDATE alliance_canon SET active = FALSE WHERE name = %s"
    for a in a_canon:
        if not a.has_key('found'):
            cursor.execute(query,(a['name'],))
            if cursor.rowcount < 1:
                raise            
            

    nxt_query="SELECT nextval('planet_canon_id_seq'::text)"
    query="INSERT INTO planet_canon (id,planetname,rulername) VALUES (%s,%s,%s)"
    for p in p_new:
        cursor.execute(nxt_query)
        next_id=cursor.dictfetchone()
        p.id=next_id['nextval']
        
        cursor.execute(query,(p.id,p.planetname,p.rulername))
        if cursor.rowcount < 1:
            raise

    nxt_query="SELECT nextval('galaxy_canon_id_seq'::text)"
    query="INSERT INTO galaxy_canon (id,x,y) VALUES (%s,%s,%s)"
    for g in g_new:
        cursor.execute(nxt_query)
        next_id=cursor.dictfetchone()
        g.id=next_id['nextval']
        cursor.execute(query,(g.id,g.x,g.y))
        if cursor.rowcount < 1:
            raise

    nxt_query="SELECT nextval('alliance_canon_id_seq'::text)"
    query="INSERT INTO alliance_canon (id,name) VALUES (%s,%s)"
    for a in a_new:
        cursor.execute(nxt_query)
        next_id=cursor.dictfetchone()
        a.id=next_id['nextval']
        
        cursor.execute(query,(a.id,a.name))
        if cursor.rowcount < 1:
            raise    

    t2=time.time()-t1
    print "Updated canonical in %.3f seconds" % (t2,)
    t1=time.time()

    query ="INSERT INTO updates "
    query+="(tick,planets,galaxies,alliances) "
    query+="VALUES (%s,%s,%s,%s)"
    cursor.execute(query,(planet_tick,len(p_list),len(g_list),len(a_list)))
    if cursor.rowcount < 1:
        raise

    query ="INSERT INTO planet_dump "
    query+="(tick,x,y,z,planetname,rulername,race,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,id) "
    query+="VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    for p in p_list:
        cursor.execute(query,(planet_tick,p.x,p.y,p.z,p.planetname,p.rulername,p.race,p.size,p.score,
                              p.value,p.score_rank,p.value_rank,p.size_rank,p.xp,p.xp_rank,p.id))
        if cursor.rowcount < 1:
            raise
    
    query ="INSERT INTO galaxy_dump "
    query+="(tick,x,y,name,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,id) "
    query+="VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    for g in g_list:
        cursor.execute(query,(galaxy_tick,g.x,g.y,g.name,g.size,g.score,g.value,g.score_rank,g.value_rank,
                              g.size_rank,g.xp,g.xp_rank,g.id))
        if cursor.rowcount < 1:
            raise

    query ="INSERT INTO alliance_dump "
    query+="(tick,name,size,members,score,score_rank,size_rank,members_rank,score_avg,size_avg,id) "
    query+="VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    for a in a_list:
        a.score_avg = a.score / a.members
        a.size_avg = a.size / a.members
        cursor.execute(query,(alliance_tick,a.name,a.size,a.members,a.score,a.score_rank,a.size_rank,
                              a.members_rank,a.score_avg,a.size_avg,a.id))
        if cursor.rowcount < 1:
            raise

    t2=time.time()-t1
    print "Inserted dumps in %.3f seconds" % (t2,)
    t1=time.time()
            
    conn.commit()

except:
    conn.rollback()
    raise

t2=time.time()-t1
t1=time.time()-t_start
print "Commit in %.3f seconds" % (t2,)
print "Total time taken: %.3f seconds" % (t1,)
"""
