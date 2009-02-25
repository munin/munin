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

# This module doesn't have anything alliance specific as far as I can tell.
# qebab, 24/6/08.

import re
from munin import loadable

class details(loadable.loadable):
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\d+)[. :-](\d+)[. :-](\d+)")
        self.usage=self.__class__.__name__ + " <x:y:z>"
        self.helptext=["This command basically collates lookup, xp, intel and status into one simple to use command. Neat, huh?"]

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        u=None
        if user:
            #irc_msg.reply("You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
            u=loadable.user(pnick=irc_msg.user)
            if not u.load_from_db(self.cursor):
                pass
                #irc_msg.reply("Usage: %s (you must be registered for automatic lookup)" % (self.usage,))
                #return 1

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables

        x=m.group(1)
        y=m.group(2)
        z=m.group(3)

        # first, plain lookup

        p=loadable.planet(x=x,y=y,z=z)
        if not p.load_most_recent(self.cursor):
            irc_msg.reply("No planet matching '%s:%s:%s' found"%(p.x,p.y,p.z,))
            return 1

        irc_msg.reply(p.__str__())

        # next we do XP



        if u.planet_id:
            # this is a straight copy from xp. Dirty dirty.
            attacker = u.planet
            reply="Target "
            victim_val = p.value
            attacker_val = attacker.value
            victim_score = p.score
            attacker_score = attacker.score

            reply+="%s:%s:%s (%s|%s) "%(p.x,p.y,p.z,
                                        self.format_value(victim_val*100),self.format_value(victim_score*100))
            reply+="| Attacker %s:%s:%s (%s|%s) "%(attacker.x,attacker.y,attacker.z,
                                                   self.format_value(attacker_val*100),self.format_value(attacker_score*100))
            total_roids = p.size

            #bravery = min(20,10*(float(victim_val)/attacker_val))
            #bravery = min(20,5*(float(victim_val)/attacker_val)*(float(victim_score)/attacker_score))

            bravery = max(0,(min(2,float(victim_val)/attacker_val)-0.4 ) * (min(2,float(victim_score)/attacker_score)-0.6))
            #bravery = max(0,min(30,10*(min(2,float(victim_val)/attacker_val)  + min(2,float(victim_score)/attacker_score) - 1)))
            bravery *= 10

            reply+="| Bravery: %.2f " % (bravery,)

            cap=total_roids/4
            xp=int(cap*bravery)
            reply+="| Roids: %s | XP: %s | Score: %s" % (cap,xp,xp*60)
            irc_msg.reply(reply)

        i=loadable.intel(pid=p.id)
        reply="Information stored for %s:%s:%s - "% (p.x,p.y,p.z)
        if i.load_from_db(self.cursor) and i.id>0:
            reply+=i.__str__()
        irc_msg.reply(reply)


        query="SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid, t2.pnick AS pnick, t2.userlevel AS userlevel, t3.x AS x, t3.y AS y, t3.z AS z"
        query+=" FROM target AS t1"
        query+=" INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
        query+=" LEFT JOIN user_list AS t2 ON t1.uid=t2.id"
        query+=" WHERE t1.tick > (SELECT MAX(tick) FROM updates) AND t3.tick = (SELECT MAX(tick) FROM updates) AND t3.x=%s AND t3.y=%s AND t3.z=%s"

        self.cursor.execute(query,(p.x,p.y,p.z))
        if self.cursor.rowcount < 1:
            reply="No bookings matching planet %s:%s:%s"%(p.x,p.y,p.z)
        else:
            reply="Status for %s:%s:%s -" % (x,y,z)
            prev=[]
            for r in self.cursor.dictfetchall():
                owner="nick:"+r['nick']
                if r['pnick']:
                    owner="user:"+r['pnick']
                    prev.append("(%s %s)" % (r['tick'],owner))

            reply+=" "+string.join(prev,', ')

        irc_msg.reply(reply)




        return 1
