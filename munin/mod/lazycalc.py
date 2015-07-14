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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

import re
import string
import munin.loadable as loadable
from robobrowser import RoboBrowser
import datetime

class lazycalc(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,100)
        self.paramre=re.compile(r"^\s*(\d+)[. :-](\d+)[. :-](\d+)\s+(\d+)")
        self.usage=self.__class__.__name__ + " <x:y:z> <eta>"
        self.helptext="Builds a calc for you lazy ass"

    def execute(self,user,access,irc_msg):
        m=self.commandre.search(irc_msg.command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        x=m.group(1)
        y=m.group(2)
        z=m.group(3)
        eta=m.group(4)

        # do stuff here

        target=loadable.planet(x=x,y=y,z=z)
        if not target.load_most_recent(self.cursor):
            irc_msg.reply("No planet matching '%s:%s:%s' found"%(x,y,z))
            return 1

        jgp=self.get_jgp(target)
        if not jgp:
            irc_msg.reply("I'd get right on that if I had a JGP from this tick. Really, I would. Right. On. That.")
            return 1

        planets=[row for row in jgp if row['eta']==int(eta)]
        aus=self.get_aus(target,planets)
        print aus
        outdated=[au for au in aus if au['age'] > 12]
        if len(outdated) > 0:
            # fixme: actually list the missing planets here
            reply=string.join(["%s:%s:%s" % (p['x'],p['y'],p['z']) for p in outdated], ", ")
            irc_msg.reply("Get off your ass and give me fresh AUs on: %s" % (reply,))
            return 1

        calc_url=self.create_calc(target,aus)
        # create calc (one AU at a time)
        # link to calc (with caveats)
        fleet_count=len(aus)-1
        irc_msg.reply("Using ancient intel from %s ago, I found %d fleet%s AND HERE'S YOUR GOD DAMNED CALC: %s" % (self.age(jgp),fleet_count,"s" if fleet_count > 1 else "",calc_url))
        return 1

    def age(self,jgp):
        if len(jgp) > 0 and jgp[0]['scan_time']:
            return str(datetime.datetime.utcnow() - jgp[0]['scan_time'])
        else:
            return "ages"

    def create_calc(self,target,aus):
        browser = RoboBrowser(user_agent='a python robot')
        browser.open('https://game.planetarion.com/bcalc.pl')
        for au in aus:
            form = browser.get_form()
            form['scans_area']="http://game.planetarion.com/showscan.pl?scan_id=" + au['rand_id']
            form['action']='add_att' if au['mission'] == 'attack' else 'add_def'
            print form
            browser.submit_form(form)
        form = browser.get_form()
        form['def_metal_asteroids']=target.size
        form['action']='save'
        browser.submit_form(form)
        return browser.url



    def get_jgp(self,p):
        query="SELECT t3.x,t3.y,t3.z,t1.tick AS tick,t1.nick,t1.scantype,t1.rand_id,t1.scan_time,t2.mission,t2.fleet_size,t2.fleet_name,t2.landing_tick-t1.tick AS eta"
        query+=" FROM scan AS t1"
        query+=" INNER JOIN fleet AS t2 ON t1.id=t2.scan_id"
        query+=" INNER JOIN planet_dump AS t3 ON t2.owner_id=t3.id"
        query+=" WHERE t1.pid=%s AND t3.tick=(SELECT max_tick())"
        query+=" AND t1.id=(SELECT id FROM scan WHERE pid=t1.pid AND scantype='jgp'"
        query+=" AND t1.tick=(SELECT max_tick())"
        query+=" ORDER BY tick DESC, id DESC LIMIT 1) ORDER BY eta ASC"
        self.cursor.execute(query,(p.id,))
        if self.cursor.rowcount < 1:
            return None
        return self.cursor.dictfetchall()

    def get_aus(self,target,planets):
        return [self.get_au(target.x,target.y,target.z,'defend')] + [self.get_au(p['x'],p['y'],p['z'],p['mission']) for p in planets]

    def get_au(self,x,y,z,mission):
        p=loadable.planet(x=x,y=y,z=z)
        base={"x": x, "y": y, "z": z}
        if not p.load_most_recent(self.cursor):
            z=base.copy()
            val=z.update({"age": 1000})
            print "returning actual value: %s\n" % (val,)
            return val
        query="SELECT max_tick() - t1.tick AS age,t1.nick,t1.scantype,t1.rand_id,t3.name,t2.amount"
        query+=" FROM scan AS t1"
        query+=" INNER JOIN au AS t2 ON t1.id=t2.scan_id"
        query+=" INNER JOIN ship AS t3 ON t2.ship_id=t3.id"
        query+=" WHERE t1.pid=%s AND t1.id=(SELECT id FROM scan WHERE pid=t1.pid"
        query+=" AND scantype='au'"
        query+=" ORDER BY tick DESC LIMIT 1)"
        self.cursor.execute(query,(p.id,))
        if self.cursor.rowcount < 1:
            val={"age": 1000}
        else:
            val=self.cursor.dictfetchone()
        val['x']=x
        val['y']=y
        val['z']=z
        val['mission']=mission
        print "returning actual value: %s\n" % val,
        return val

