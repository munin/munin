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

import os, re, psycopg, time

conn=psycopg.connect("dbname=patools16 user=andreaja host=10.0.0.5 ")
cursor=conn.cursor()

solutions=[]

#planets=[{'x:':-1,'y':-1,'z':-1,'score':0,'size':0}]
planets=[]
query="SELECT x,y,z, score, size FROM planet_dump WHERE tick=(SELECT MAX(tick) FROM updates) ORDER BY random()"
cursor.execute(query)
for p in cursor.dictfetchall():
    planets.append({'x':p['x'],'y':p['y'],'z':p['z'],'score':p['score'],'size':p['size']})



def perm(index,max_score,max_size,max_members,endset):
    global solutions,planets
    print "Entering perm with score: %s,size: %s,members: %s" %( max_score,max_size,max_members)        
    endset.append(index)
    max_score-=planets[index]['score']
    max_size-=planets[index]['size']
    max_members-=1
    
    if max_members == max_size == max_score == 0:
        solutions.append(list(endset))
    elif max_members == 0:
        pass
    else:
        print "%s %s %s" %( max_score,max_size,max_members)
        for i in range(index+1,len(planets)):
            if index==0:
                print "Recursing for %s" % (i,)
            else:
                print "Index: %s, MaxMem: %s" % (index,max_members)
            perm(i,max_score,max_size,max_members,endset)
    max_score+=planets[index]['score']
    max_size+=planets[index]['size']
    max_members+=1        
    endset.pop()


query="SELECT name,size,score,members FROM alliance_dump WHERE tick=(SELECT MAX(tick) FROM updates) ORDER BY members ASC"
cursor.execute(query)
for a in cursor.dictfetchall():
    solutions=[]
    print "Beginning recursion for %s with score: %s, size: %s and members: %s" %( a['name'],a['score'],a['size'],a['members'])
    perm(0,a['score'],a['size'],a['members']+1,[])
    if not len(solutions):
        print "Uh oh, could not find a valid list for alliance %s " % (a['name'],)
    else:
        print "Found %s results for alliance %s" % (len(solutions),a['name'])
    print solutions
    time.sleep(10)




"""
T=[]
planets=[]

query="SELECT MAX(size) AS max FROM alliance_dump WHERE tick=(SELECT max(tick) FROM updates)"
cursor.execute(query)
max_size=cursor.dictfetchone()['max']

def Q(i,s):
    global planets, T, max_size
    if i==0:
        if planets[i]['size']==s:
            T[i][s]+=1
        return
    #    for j in range(i-1,-1,-1):
    if T[i-1][s-planets[i]['size']]>0:
        T[i][s]=T[i-1][s-planets[i]['size']]+1
    elif T[i-1][s]:
        T[i][s]=T[i-1][s]

query="SELECT x,y,z, score, size FROM planet_dump WHERE tick=(SELECT max(tick) FROM updates) ORDER BY size ASC "
cursor.execute(query)
for p in cursor.dictfetchall():
    planets.append({'x':p['x'],'y':p['y'],'z':p['z'],'score':p['score'],'size':p['size']})
    T.append([0]*(max_size+1))
    #print p

st_gen=time.time()

for i in range(len(planets)):
    start=time.time()
    s=planets[i]['size']
    while s+planets[i]['size']<=max_size:
        Q(i,s)
        s+=1
    print "Completed %s in %.3f seconds" % (i,(time.time()-start))
    if i % 100 == 0:
        print "SO FAR i=%s %.3f seconds" % (i,(time.time()-st_gen))
        

print "Completed all in %s seconds" % ((time.time()-st_gen))
"""
"""
def xuniqueCombinations(items, n): 
    if n==0: yield []
    else:
        for i in xrange(len(items)):
            for cc in xuniqueCombinations(items[i+1:],n-1):
                yield [items[i]]+cc

alliances=[]
query="SELECT name,size,score,members FROM alliance_dump WHERE tick=(SELECT MAX(tick) FROM updates) AND members > 1 ORDER BY members ASC"
cursor.execute(query)
for a in cursor.dictfetchall():
    planets=[]
    query="SELECT x,y,z, score, size FROM planet_dump WHERE tick=(SELECT MAX(tick) FROM updates) ORDER BY random()"
    cursor.execute(query)
    for p in cursor.dictfetchall():
        planets.append({'x':p['x'],'y':p['y'],'z':p['z'],'score':p['score'],'size':p['size']})
    for i in xuniqueCombinations(planets,a['members']):
        print i
        tot_size=0
        tot_score=0
        tot_mem=0
        for p in i:
            tot_size+=p['size']
            tot_score+=p['score']
            if tot_size>a['size']:
                break
            elif tot_score>a['score']:
                break
            tot_mem+=1
        if tot_size==a['size'] and tot_score==a['score'] and tot_mem==a['members']:
            print "%s (%s) | %s" % (a['name'],a['members'], i)
            break
            
""" 


"""
class B:
    def __init__(self):
        print "B"

def reg_controllers():
    files=os.listdir("crap")
    sources=[]
    obj_list=[]
    pyre=re.compile(r"(.*)\.py$",re.I)
    for f in files:
        m=pyre.search(f)
        if m:
            sources.append(m.group(1))

    for source in sources:
        filename=os.path.join("crap", source+'.py')
        execfile(filename)
        obj_list.append(locals().get(source)())

    print obj_list
#    print locals()
#    if callable(locals().get('A')):
#        print "Pie!"
#    test = locals().get('A')()

reg_controllers()
"""
