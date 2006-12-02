"""
Loadable.Loadable subclass
"""

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

class galpenis(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + " <x:y>"
        
    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        m=self.coordre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,self.usage)
            return 0
        x=m.group(1)
        y=m.group(2)
                                      
        #search=user or nick
        #m=self.paramre.search(m.group(1))
        #if m:
        #    search=m.group(2) or search


        query="DROP TABLE galpenis;DROP SEQUENCE gal_xp_gain_rank;DROP SEQUENCE gal_value_diff_rank;DROP SEQUENCE gal_activity_rank;"
        try:
            self.cursor.execute(query)
        except:            
            pass



        query="CREATE TEMP SEQUENCE gal_xp_gain_rank;CREATE TEMP SEQUENCE gal_value_diff_rank;CREATE TEMP SEQUENCE gal_activity_rank"
        self.cursor.execute(query)
        query="SELECT setval('gal_xp_gain_rank',1,false); SELECT setval('gal_value_diff_rank',1,false); SELECT setval('gal_activity_rank',1,false)"
        self.cursor.execute(query)

            
        query="CREATE TEMP TABLE galpenis AS"
        query+=" (SELECT *,nextval('gal_activity_rank') AS activity_rank"
        query+=" FROM (SELECT  *,nextval('gal_value_diff_rank') AS value_diff_rank"
        query+=" FROM (SELECT *,nextval('gal_xp_gain_rank') AS xp_gain_rank"
        query+=" FROM (SELECT t1.x AS x,t1.y AS y,t1.name AS name,t1.xp-t5.xp AS xp_gain, t1.score-t5.score AS activity, t1.value-t5.value AS value_diff"
        query+=" FROM galaxy_dump AS t1"
#        query+=" INNER JOIN intel AS t2 ON t1.id=t2.pid"
#        query+=" LEFT JOIN user_pref AS t3 ON t2.pid=t3.planet_id"
#        query+=" LEFT JOIN user_list AS t4 ON t2.pid=t4.planet_id"
        query+=" INNER JOIN galaxy_dump AS t5"
        query+=" ON t1.id=t5.id AND t1.tick - 72 = t5.tick"
        query+=" WHERE t1.tick = (select max(tick) from updates)"
#        query+=" AND t2.alliance ILIKE '%asc%'"
        query+=" ORDER BY xp_gain DESC) AS t6"
        query+=" ORDER BY value_diff DESC) AS t7"
        query+=" ORDER BY activity DESC) AS t8)"


        self.cursor.execute(query)

        query="SELECT x,y,name,xp_gain,activity,value_diff,xp_gain_rank,value_diff_rank,activity_rank"
        query+=" FROM galpenis"
        query+=" WHERE x = %s AND y = %s"
#        query="SELECT nick,pnick,xp_gain,activity,value_diff,xp_gain_rank,value_diff_rank,activity_rank"
#        query+=" FROM epenis"
#        query+=" WHERE pnick ILIKE %s"


        self.cursor.execute(query,(x,y))
        if self.cursor.rowcount < 1:
            reply="No galpenis stats matching %s:%s"% (x,y)

        res=self.cursor.dictfetchone()
        if not res:
            reply="No galpenis stats matching %s:%s"% (x,y)
        else:
            person=res['name'] or res['x'] + res['y']
            reply ="galpenis for '%s' is %s score long. This makes %s:%s rank: %s for galpenis in the universe!" % (person,res['activity'],x,y,res['activity_rank'])

        self.client.reply(prefix,nick,target,reply)
        
        return 1

                                                                                                                                            
