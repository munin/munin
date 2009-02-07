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

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08

class apenis(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^(\s+(\S+))?")
        self.usage=self.__class__.__name__ + " <alliance>"
        
    def execute(self,nick,username,host,target,prefix,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        
        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply(self.usage)
            return 0

        search=m.group(2)
        u=loadable.user(pnick=user)
        if search is not None:
            a=loadable.alliance(name=search)
            if not a.load_most_recent(self.conn,irc_msg.client,self.cursor):
                reply="No alliances match %s" % (search,)
                irc_msg.reply(reply)
                return 1
        elif u.load_from_db(self.conn,irc_msg.client,self.cursor) and u.userlevel >= 100:
            a=loadable.alliance(name=self.config.get('Auth', 'alliance'))
            if not a.load_most_recent(self.conn,irc_msg.client,self.cursor):
                reply="No alliances match %s" % (search,)
                irc_msg.reply(reply)
                return 1
        elif u.id > -1 and u.planet is not None:
            i=loadable.intel(pid=p.id)
            if (not i.load_from_db(self.conn,irc_msg.client,self.cursor)) or i.alliance is None:
                reply="Make sure you've set your planet with !pref and alliance with !intel"
                irc_msg.reply(reply)
                return 1
            else:
                a=loadable.alliance(name=i.alliance)
        else:
            reply="Make sure you've set your planet with !pref and alliance with !intel"
            irc_msg.reply(reply)
            return 1

        query="DROP TABLE apenis;DROP SEQUENCE al_activity_rank;"
        try:
            self.cursor.execute(query)
        except:
            pass

        query="CREATE TEMP SEQUENCE al_activity_rank"
        self.cursor.execute(query)
        query="SELECT setval('al_activity_rank',1,false)"
        self.cursor.execute(query)


        query="CREATE TEMP TABLE apenis AS"
        query+=" (SELECT *,nextval('al_activity_rank') AS activity_rank"
        query+=" FROM (SELECT t1.name, t1.members, t1.score-t5.score AS activity"
        query+=" FROM alliance_dump AS t1"
        query+=" INNER JOIN alliance_dump AS t5"
        query+=" ON t1.id=t5.id AND t1.tick - 72 = t5.tick"
        query+=" WHERE t1.tick = (select max(tick) from updates)"
        query+=" ORDER BY activity DESC) AS t8)"
        
        self.cursor.execute(query)

        query="SELECT name,activity,activity_rank,members"
        query+=" FROM apenis"
        query+=" WHERE name ILIKE %s"

        self.cursor.execute(query,(a.name,))
        if self.cursor.rowcount < 1:
            query="SELECT name,activity,activity_rank"
            query+=" FROM apenis"
            query+=" WHERE name ILIKE %s"
            
            self.cursor.execute(query,(a.name,))

        res=self.cursor.dictfetchone()
        if not res:
            reply="No apenis stats matching %s"% (a.name,)
        else:
            person=res['name']
            reply ="apenis for %s is %s score long. This makes %s rank: %s apenis. The average peon is sporting a %s score epenis." % (person,res['activity'],person,res['activity_rank'],int(res['activity']/res['members']))

        irc_msg.reply(reply)
        
        return 1

                                                                                                                                            
