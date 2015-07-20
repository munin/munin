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
import threading
import datetime
import time
import operator

def timefunc(f):
    def f_timer(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        print f.__name__, 'took', end - start, 'time'
        return result
    return f_timer


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
        fleet_count=len(aus)-1
        if fleet_count > 10:
            irc_msg.reply("This is going to take a moment, %s"% (irc_msg.nick,))
        calc_creator(target,aus,jgp,fleet_count,irc_msg).start()
        return 1


    @timefunc
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

    @timefunc
    def get_au(self,x,y,z,mission):
        p=loadable.planet(x=x,y=y,z=z)
        base={"x": x, "y": y, "z": z}
        if not p.load_most_recent(self.cursor):
            z=base.copy()
            val=z.update({"age": 1000})
            print "returning actual value: %s\n" % (val,)
            return val
        query="SELECT max_tick() - t1.tick AS age,t1.rand_id"
        query+=" FROM scan AS t1"
        query+=" WHERE t1.pid=%s"
        query+=" AND scantype='au'"
        query+=" ORDER BY tick DESC LIMIT 1"

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

class calc_creator(threading.Thread):
    def __init__(self,target,aus,jgp,fleet_count,irc_msg):
        self.target=target
        self.aus=aus
        self.jgp=jgp
        self.fleet_count=fleet_count
        self.irc_msg=irc_msg
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.unsafe_method()
        except Exception, e:
            irc_msg.reply("Error in module '%s'. Please report the command you used to the bot owner as soon as possible."%(irc_msg.command_name,))


    def unsafe_method(self):
        calc_url=self.create_calc(self.target,self.aus)
        self.irc_msg.reply("Using ancient intel from %s ago, I found %d fleet%s AND HERE'S YOUR GOD DAMNED CALC: %s" % (self.age(self.jgp),self.fleet_count,"s" if self.fleet_count > 1 else "",calc_url))

    def age(self,jgp):
        if len(jgp) > 0 and jgp[0]['scan_time']:
            return str(datetime.datetime.utcnow() - jgp[0]['scan_time'])
        else:
            return "ages"
    @timefunc
    def create_calc(self,target,aus):
        browser = RoboBrowser(user_agent='a python robot', history=False)
        browser.open('https://game.planetarion.com/bcalc.pl')
        for au in sorted(aus,key=operator.itemgetter('x','y','z')):
            self.add_au(browser,au)
        form = browser.get_form()
        form['def_metal_asteroids']=target.size
        form['action']='save'
        browser.submit_form(form)
        return browser.url

    @timefunc
    def add_au(self,browser,au):
        form = browser.get_form()
        form['scans_area']="http://game.planetarion.com/showscan.pl?scan_id=" + au['rand_id']
        form['action']='add_att' if au['mission'] == 'attack' else 'add_def'
        browser.submit_form(form)

