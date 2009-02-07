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

# Removed alliance specific things from this module.
# qebab 24/6/08.

class epenis(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.paramre=re.compile(r"^(\s+(\S+))?")
        self.usage=self.__class__.__name__ + ""
        
    def execute(self,nick,target,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        search=user or nick
        m=self.paramre.search(m.group(1))

        if m:
            search=m.group(2) or search


        query="DROP TABLE epenis;"
        try:
            self.cursor.execute(query)
        except:
            pass

        query="DROP SEQUENCE xp_gain_rank;DROP SEQUENCE value_diff_rank;DROP SEQUENCE activity_rank;"
        try:
            self.cursor.execute(query)
        except:
            pass

        query="CREATE TEMP SEQUENCE xp_gain_rank;CREATE TEMP SEQUENCE value_diff_rank;CREATE TEMP SEQUENCE activity_rank"
        self.cursor.execute(query)
        query="SELECT setval('xp_gain_rank',1,false); SELECT setval('value_diff_rank',1,false); SELECT setval('activity_rank',1,false)"
        self.cursor.execute(query)

            
        query="CREATE TABLE epenis AS"
        query+=" (SELECT *,nextval('activity_rank') AS activity_rank"
        query+=" FROM (SELECT  *,nextval('value_diff_rank') AS value_diff_rank"
        query+=" FROM (SELECT *,nextval('xp_gain_rank') AS xp_gain_rank"
        query+=" FROM (SELECT t2.nick, t4.pnick ,t1.xp-t5.xp AS xp_gain, t1.score-t5.score AS activity, t1.value-t5.value AS value_diff"
        query+=" FROM planet_dump AS t1"
        query+=" INNER JOIN intel AS t2 ON t1.id=t2.pid"
#        query+=" LEFT JOIN user_pref AS t3 ON t2.pid=t3.planet_id"
        query+=" LEFT JOIN user_list AS t4 ON t1.id=t4.planet_id"
        query+=" INNER JOIN planet_dump AS t5"
        query+=" ON t1.id=t5.id AND t1.tick - 72 = t5.tick"
        query+=" LEFT JOIN alliance_canon AS t6 ON t2.alliance_id=t6.id"
        query+=" WHERE t1.tick = (select max(tick) from updates)"
        query+=" AND t6.name ILIKE %s"
        query+=" ORDER BY xp_gain DESC) AS t6"
        query+=" ORDER BY value_diff DESC) AS t7"
        query+=" ORDER BY activity DESC) AS t8)"

        self.cursor.execute(query, (self.config.get('Auth', 'alliance'),))

        query="SELECT nick,pnick,xp_gain,activity,value_diff,xp_gain_rank,value_diff_rank,activity_rank"
        query+=" FROM epenis"
        query+=" WHERE pnick ILIKE %s"

        self.cursor.execute(query,(search,))
        if self.cursor.rowcount < 1:
            query="SELECT nick,pnick,xp_gain,activity,value_diff,xp_gain_rank,value_diff_rank,activity_rank"
            query+=" FROM epenis"
            query+=" WHERE nick ILIKE %s"
            
            self.cursor.execute(query,('%'+search+'%',))

        res=self.cursor.dictfetchone()
        if not res:
            reply="No epenis stats matching %s"% (search,)
        else:
            person=res['pnick'] or res['nick']
            reply ="epenis for %s is %s score long. This makes %s rank: %s for epenis in %s!" % (person,res['activity'],person,res['activity_rank'],
                                                                                                 self.config.get('Auth', 'alliance'))

        irc_msg.reply(reply)
        
        return 1
