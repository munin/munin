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

# Switched hardcoded owner nick for config.get('Auth', 'owner_nick').
# Shouldn't be anything jester/ascendancy dependent left
# qebab, 24/6/08.

class gangbang(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.paramre=re.compile(r"^\s+(\D\S*)(\s+(\d+))?")
        self.usage=self.__class__.__name__ + " [alliance] [tick]"
        
    def execute(self,nick,target,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        curtick=self.current_tick()


        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        # assign param variables

        subject=m.group(1)
        when=m.group(3)
        if when: when=int(when)
        if subject: subject=subject.strip()

        a=loadable.alliance(name=subject)
        if not a.load_most_recent(irc_msg.client,self.cursor):
            irc_msg.reply("'%s' is not a valid alliance."%(subject,))
            return 1

        if when and when < 80:
            tick=curtick+when
        elif when and when < curtick:
            irc_msg.reply("Can not check status on the past. You wanted tick %s, but current tick is %s. (If you really need to know, poke %s.)"%(when,curtick, self.config.get('Auth', 'owner_nick')))
            return 1
        elif when:
            tick=when

        args=()
        query="SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid, t2.pnick AS pnick, t2.userlevel AS userlevel, t3.x AS x, t3.y AS y, t3.z AS z"
        query+=" FROM target AS t1"
        query+=" INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
        query+=" LEFT JOIN user_list AS t2 ON t1.uid=t2.id"
        query+=" INNER JOIN intel AS t4 ON t1.pid=t4.pid"
        query+=" WHERE"

        if when:
            query+=" t1.tick = %s"
            args+=(tick,)
        else:
            query+=" t1.tick > (SELECT MAX(tick) FROM updates)"

        query+=" AND t3.tick = (SELECT MAX(tick) FROM updates)"
        query+=" AND t4.alliance_id = %s"
        query+=" ORDER BY tick, x, y, z"
        self.cursor.execute(query,args+(a.id,))

        if self.cursor.rowcount < 1:
            reply="No active bookings matching alliance %s" %(a.name)
            if when:
                reply+=" for tick %s"%(tick,)
            irc_msg.reply(reply)
            return 1

        ticks={}
        for r in self.cursor.dictfetchall():
            if not ticks.has_key(r['tick']):
                ticks[r['tick']]=[]
            ticks[r['tick']].append(r)

        reply="Target information for %s"%(a.name)
        if when:
            reply+=" for landing on tick %s (eta %s):"%(tick,tick-curtick)
        sorted_keys=ticks.keys()
        sorted_keys.sort()
        for k in sorted_keys:
            reply=string.join([reply,"Tick %s (eta %s)" % (k,k-curtick)])
            booked_list=ticks[k]
            prev=[]
            for p in booked_list:
                owner="nick:"+p['nick']
                if p['pnick']:
                    owner="user:"+p['pnick']
                prev.append("(%s:%s:%s %s)" % (p['x'],p['y'],p['z'],owner))


            reply+=" "+string.join(prev,', ')
            irc_msg.reply(reply.strip())
            reply=""
        return 1

