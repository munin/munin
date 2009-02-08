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

class bitches(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.paramre=re.compile(r"^\s+(\d+)")
        self.usage=self.__class__.__name__ + " [minimum eta]"

    def execute(self,target,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        
        # do stuff here
        args=()
        query="SELECT t3.x AS x, t3.y AS y, count(*) AS number"
        query+=" FROM target AS t1"
        query+=" INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
        query+=" LEFT JOIN user_list AS t2 ON t1.uid=t2.id"

        m=self.paramre.search(m.group(1))
        tick=None
        if m:
            tick=m.group(1)
            query+=" WHERE t1.tick >= ((SELECT MAX(tick) FROM updates)+%s)"
            args+=(m.group(1),)
        else:
            query+=" WHERE t1.tick > (SELECT MAX(tick) FROM updates)"
        query+="  AND t3.tick = (SELECT MAX(tick) FROM updates)"
        query+=" GROUP BY x, y ORDER BY x, y"


            

        self.cursor.execute(query,args)
        if self.cursor.rowcount < 1:
            reply="No active bookings. This makes Munin sad. Please don't make Munin sad."
            irc_msg.reply(reply)
            return 1
        reply="Active bookings:"
        prev=[]
        for b in self.cursor.dictfetchall():
            prev.append("%s:%s(%s)"%(b['x'],b['y'],b['number']))

        reply+=" "+string.join(prev,', ')
        irc_msg.reply(reply)


        #begin finding of all alliance targets

        args=()
        query="SELECT lower(t6.name) AS alliance,count(*) AS number"
        query+=" FROM target AS t1"
        query+=" INNER JOIN planet_dump AS t3 on t1.pid=t3.id"
        query+=" LEFT JOIN intel AS t2 ON t3.id=t2.pid"
        query+=" LEFT JOIN alliance_canon AS t6 ON t2.alliance_id=t6.id"
        if tick:
            query+=" WHERE t1.tick >= ((SELECT MAX(tick) FROM updates)+%s)"
            args+=(tick,)
        else:
            query+=" WHERE t1.tick > (SELECT MAX(tick) FROM updates)"
        query+="  AND t3.tick = (SELECT MAX(tick) FROM updates)"
        query+=" GROUP BY lower(t6.name) ORDER BY lower(t6.name)"
        self.cursor.execute(query,args)

        if self.cursor.rowcount < 1:
            "This should never happen"
        reply="Active bitches:"
        prev=[]
        for b in self.cursor.dictfetchall():
            prev.append("%s (%s)"%(self.cap(b['alliance'] or "Unknown"),b['number']))
        reply+=" "+string.join(prev,', ')
        irc_msg.reply(reply)
        
        return 1
