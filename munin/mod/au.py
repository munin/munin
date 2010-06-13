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

import re
import string
from munin import loadable

class au(loadable.loadable):
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,50)
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + ""
        self.helptext=None

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
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
        params=m.group(1)
        m=self.planet_coordre.search(params)

        reply=""
        if m:
            x=m.group(1)
            y=m.group(2)
            z=m.group(3)

            p=loadable.planet(x=x,y=y,z=z)
            if not p.load_most_recent(self.cursor):
                irc_msg.reply("No planet matching '%s:%s:%s' found"%(x,y,z))
                return 1

            query="SELECT t1.tick,t1.nick,t1.scantype,t1.rand_id,t3.name,t2.amount"
            query+=" FROM scan AS t1"
            query+=" INNER JOIN au AS t2 ON t1.id=t2.scan_id"
            query+=" INNER JOIN ship AS t3 ON t2.ship_id=t3.id"
            query+=" WHERE t1.pid=%s AND t1.id=(SELECT id FROM scan WHERE pid=t1.pid AND scantype='au' ORDER BY tick DESC LIMIT 1)"
            self.cursor.execute(query,(p.id,))

            if self.cursor.rowcount < 1:
                reply+="No advanced unit scans available on %s:%s:%s" % (p.x,p.y,p.z)
            else:

                reply+="Newest advanced unit scan on %s:%s:%s" % (p.x,p.y,p.z)

                prev=[]
                for s in self.cursor.dictfetchall():
                    prev.append("%s %s" % (s['name'],s['amount']))
                    tick=s['tick']
                    rand_id=s['rand_id']

                reply+=" (id: %s, age: %s, value diff: %s) " % (rand_id,self.current_tick()-tick,p.vdiff(self.cursor,tick))
                reply+=string.join(prev,' | ')
        else:
            m=self.idre.search(params)
            if not m:
                irc_msg.reply("Usage: %s" % (self.usage,))
                return 0

            rand_id=m.group(1)

            query="SELECT t4.x,t4.y,t4.z,t1.tick,t1.nick,t1.scantype,t1.rand_id,t3.name,t2.amount,t4.value-t5.value AS vdiff"
            query+=" FROM scan AS t1"
            query+=" INNER JOIN au AS t2 ON t1.id=t2.scan_id"
            query+=" INNER JOIN ship AS t3 ON t2.ship_id=t3.id"
            query+=" INNER JOIN planet_dump AS t4 ON t1.pid=t4.id"
            query+=" INNER JOIN planet_dump AS t5 ON t1.pid=t5.id AND t1.tick=t5.tick"
            query+=" WHERE t4.tick=(SELECT max_tick()) AND t1.rand_id=%s"
            self.cursor.execute(query,(rand_id,))

            if self.cursor.rowcount < 1:
                reply+="No planet scans matching ID %s" % (rand_id,)
            else:
                reply+="Newest advanced unit scan on "

                prev=[]
                for s in self.cursor.dictfetchall():
                    prev.append("%s %s" % (s['name'],s['amount']))
                    tick=s['tick']
                    x=s['x']
                    y=s['y']
                    z=s['z']
                    vdiff=s['vdiff']

                reply+="%s:%s:%s (id: %s, age: %s, value diff: %s) " % (x,y,z,rand_id,self.current_tick()-tick,vdiff)
                reply+=string.join(prev,' | ')
        irc_msg.reply(reply)
        return 1




