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

# Nothing hardcoded found here.
# qebab, 24/6/08.

import re
from munin import loadable

class xp(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,1)
        self.paramre=re.compile(r"^\s+(.*)")
        #self.firstcountre=re.compile(r"^(\d+)\s+(.*)")
        self.countre=re.compile(r"^(\d+)(\.|-|:|\s*)(.*)")
        self.usage=self.__class__.__name__ + " <x:y:z> <a:b:c>"

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        params=m.group(1)

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        roid_count = -1

        victim = None
        attacker = None

        #m=self.countre.search(params)
        #if m and not ':.-'.rfind(m.group(2))>-1:
        #    roid_count=int(m.group(1))
        #    params=m.group(3)

        m=self.planet_coordre.search(params)
        if m:
            victim = loadable.planet(x=m.group(1),y=m.group(2),z=m.group(3))
            if not victim.load_most_recent(self.cursor):
                irc_msg.reply("%s:%s:%s is not a valid planet" % (victim.x,victim.y,victim.z))
                return 1
            params=params[m.end():]

        m=self.planet_coordre.search(params)
        if m:
            attacker = loadable.planet(x=m.group(1),y=m.group(2),z=m.group(3))
            if not attacker.load_most_recent(self.cursor):
                irc_msg.reply("%s:%s:%s is not a valid planet" % (attacker.x,attacker.y,attacker.z))
                return 1
            params=params[m.end():]

        if not victim:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 1

        if victim and not attacker:
            u=loadable.user(pnick=irc_msg.user)
            if not u.load_from_db(self.cursor):
		irc_msg.reply("You must be registered to use the automatic "+self.__class__.__name__+" command (log in with P and set mode +x, then make sure your planet is set with the pref command)")
                #irc_msg.reply("Usage: %s (you must be registered for automatic lookup)" % (self.usage,))
                return 1
            if u.planet_id:
                attacker = u.planet
            else:
                irc_msg.reply("Usage: %s (you must be registered for automatic lookup)" % (self.usage,))
                return 1

        if roid_count > -1:
            reply="Capturing %s roids " % (roid_count,)
            victim_val = victim.value
            victim_score = victim.score
            reply+="from %s:%s:%s (%s|%s) "%(victim.x,victim.y,victim.z,
                                          self.format_value(victim_val*100),self.format_value(victim_score*100))

            attacker_val = attacker.value
            attacker_score = attacker.score
            reply+="will earn %s:%s:%s (%s|%s) "%(attacker.x,attacker.y,attacker.z,
                                               self.format_value(attacker_val*100),self.format_value(attacker_score*100))

            #bravery = max(0,min(30,10*(min(2,float(victim_val)/attacker_val)  + min(2,float(victim_score)/attacker_score) - 1)))
            #bravery = min(20,5*(float(victim_val)/attacker_val)*(float(victim_score)/attacker_score))

            bravery = max(0,(min(2,float(victim_val)/attacker_val)-0.1 ) * (min(2,float(victim_score)/attacker_score)-0.2))
            bravery *= 10
            xp=int(bravery*roid_count)

            #xp=int(roid_count*10
            #reply+="XP: %s, Score: %s "%(xp, xp*5)
            #(Bravery: %.2f)" % (xp,xp*50,bravery)
            reply+="XP: %s, Score: %s (Bravery: %.2f)" % (xp,xp*60,bravery)
            irc_msg.reply(reply)
        else:
            reply="Target "
            victim_val = victim.value
            attacker_val = attacker.value
            victim_score = victim.score
            attacker_score = attacker.score

            reply+="%s:%s:%s (%s|%s) "%(victim.x,victim.y,victim.z,
                                     self.format_value(victim_val*100),self.format_value(victim_score*100))
            reply+="| Attacker %s:%s:%s (%s|%s) "%(attacker.x,attacker.y,attacker.z,
                                                self.format_value(attacker_val*100),self.format_value(attacker_score*100))
            total_roids = victim.size

            #bravery = min(20,10*(float(victim_val)/attacker_val))
            #bravery = max(0,min(30,10*(min(2,float(victim_val)/attacker_val) ) + (min(2,float(victim_score)/attacker_score))) - 1)
            #*(float(victim_val)/attacker_val)*(float(victim_score)/attacker_score))
            #bravery = max(0,min(30,10*(min(2,float(victim_val)/attacker_val)  + min(2,float(victim_score)/attacker_score) - 1)))


            bravery = max(0,(min(2,float(victim_val)/attacker_val)-0.1 ) * (min(2,float(victim_score)/attacker_score)-0.2))
            bravery *= 10



            reply+="| Bravery: %.2f " % (bravery,)

            cap=total_roids/4
            xp=int(cap*bravery)
            reply+="| Roids: %s | XP: %s | Score: %s" % (cap,xp,xp*60)
            irc_msg.reply(reply)


        return 1
