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


class planet(loadable.loadable):
    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 50)
        self.paramre = re.compile(r"^\s+(.*)")
        self.usage = self.__class__.__name__ + "<<x>:<y>:<z>|<id>>"
        self.helptext = None

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        params = m.group(1)
        m = self.planet_coordre.search(params)

        reply = ""
        if m:
            x = m.group(1)
            y = m.group(2)
            z = m.group(3)

            p = loadable.planet(x=x, y=y, z=z)
            if not p.load_most_recent(self.cursor, irc_msg.round):
                irc_msg.reply("No planet matching '%s:%s:%s' found" % (x, y, z))
                return 1

            query = "SELECT tick,nick,scantype,rand_id,timestamp,roid_metal,roid_crystal,roid_eonium,res_metal,res_crystal,res_eonium"
            query += ", prod_res,agents,guards"
            query += " FROM scan AS t1 INNER JOIN planet AS t2 ON t1.id=t2.scan_id"
            query += " WHERE t1.pid=%s AND t1.round=%s ORDER BY timestamp DESC"
            self.cursor.execute(query, (p.id, irc_msg.round,))

            if self.cursor.rowcount < 1:
                reply += "No planet scans available on %s:%s:%s" % (p.x, p.y, p.z)
            else:
                s = self.cursor.dictfetchone()
                reply += "Newest planet scan on %s:%s:%s (id: %s, pt: %s)" % (
                    p.x,
                    p.y,
                    p.z,
                    s["rand_id"],
                    s["tick"],
                )
                reply += (
                    " Roids: (m:%s, c:%s, e:%s) | Resources: (m:%s, c:%s, e:%s)"
                    % (
                        s["roid_metal"],
                        s["roid_crystal"],
                        s["roid_eonium"],
                        s["res_metal"],
                        s["res_crystal"],
                        s["res_eonium"],
                    )
                )
                reply += " | Hidden: %s | Agents: %s | Guards: %s" % (
                    s["prod_res"],
                    s["agents"],
                    s["guards"],
                )
                i = 0
                reply += " | Older scans: "
                prev = []
                for s in self.cursor.dictfetchall():
                    i += 1
                    if i > 4:
                        break
                    prev.append("(%s,pt%s)" % (s["rand_id"], s["tick"]))
                reply += ", ".join(prev)

        else:
            m = self.idre.search(params)
            if not m:
                irc_msg.reply("Usage: %s" % (self.usage,))
                return 0

            rand_id = m.group(1)

            query = "SELECT x,y,z,t1.tick AS tick,nick,scantype,rand_id,timestamp,roid_metal,roid_crystal,roid_eonium,res_metal,res_crystal,res_eonium"
            query += ", prod_res,agents,guards"
            query += " FROM scan AS t1 INNER JOIN planet AS t2 ON t1.id=t2.scan_id"
            query += " INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
            query += " WHERE t3.tick=(SELECT max_tick(%s::smallint)) AND t3.round=%s AND t1.rand_id=%s ORDER BY timestamp DESC"
            self.cursor.execute(query, (irc_msg.round, irc_msg.round, rand_id,))

            if self.cursor.rowcount < 1:
                reply += "No planet scans matching ID %s" % (rand_id,)
            else:
                s = self.cursor.dictfetchone()
                reply += "Newest planet scan on %s:%s:%s (id: %s, pt: %s)" % (
                    s["x"],
                    s["y"],
                    s["z"],
                    s["rand_id"],
                    s["tick"],
                )
                reply += (
                    " Roids: (m:%s, c:%s, e:%s) | Resources: (m:%s, c:%s, e:%s)"
                    % (
                        s["roid_metal"],
                        s["roid_crystal"],
                        s["roid_eonium"],
                        s["res_metal"],
                        s["res_crystal"],
                        s["res_eonium"],
                    )
                )
                reply += " | Hidden: %s | Agents: %s | Guards: %s" % (
                    s["prod_res"],
                    s["agents"],
                    s["guards"],
                )

        irc_msg.reply(reply)
        return 1
