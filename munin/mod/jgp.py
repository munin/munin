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

# Nothing alliance specific found in this module.
# qebab, 24/6/08.

import re
from munin import loadable


class jgp(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 50)
        self.paramre = re.compile(r"^\s*([0-9:. -]*|[0-9A-Za-z]*)(?:\s(l|li|lin|link|linkie))?$")
        self.usage = self.__class__.__name__ + " <coords> [link]"
        self.helptext = "Retrieve the most recent JGP on the given coords. Add 'link' to request a link instead of a data dump"

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        params = m.group(1)
        link = True if m.group(2) else False

        reply = ""

        m = self.planet_coordre.search(params)
        query_executed = False
        if m:
            x = m.group(1)
            y = m.group(2)
            z = m.group(3)

            p = loadable.planet(x=x, y=y, z=z)
            if not p.load_most_recent(self.cursor, irc_msg.round):
                irc_msg.reply("No planet matching '%s:%s:%s' found" % (x, y, z))
                return 1

            query = "SELECT p.x,p.y,p.z,"
            query += "s.tick AS tick,s.nick,s.scantype,s.rand_id,"
            query += "f.mission,f.fleet_size,f.fleet_name,f.landing_tick-s.tick AS eta"
            query += " FROM scan AS s"
            query += " INNER JOIN fleet AS f ON s.id=f.scan_id"
            query += " INNER JOIN planet_dump AS p ON f.owner_id=p.id"
            query += " WHERE s.pid=%s AND p.tick=(SELECT max_tick(%s::smallint)) AND p.round=%s"
            query += (
                " AND s.id=(SELECT id FROM scan WHERE pid=s.pid AND scantype='jgp'"
            )
            query += " ORDER BY tick DESC, id DESC LIMIT 1) ORDER BY eta ASC"
            self.cursor.execute(query, (p.id, irc_msg.round, irc_msg.round,))
            if self.cursor.rowcount > 0:
                results = self.cursor.fetchall()
                s = results[0]
                irc_msg.reply(self.reply_jgp(link,
                                             s["rand_id"],
                                             x,
                                             y,
                                             z,
                                             results,
                                             s["tick"]))
            else:
                irc_msg.reply("No JGP scans available on %s:%s:%s" % (x, y, z))
                return 0
        else:
            m = self.idre.search(params)
            if not m:
                irc_msg.reply("Usage: %s" % (self.usage,))
                return 0

            rand_id = m.group(1)

            query = "SELECT p1.x AS targ_x,p1.y AS targ_y,p1.z AS targ_z,"
            query += "s.tick,s.nick,s.scantype,s.rand_id,"
            query += "f.mission,f.fleet_size,f.fleet_name,f.landing_tick-s.tick AS eta,"
            query += "p2.x AS x,p2.y AS y,p2.z AS z"
            query += " FROM scan AS s"
            query += " INNER JOIN fleet AS f ON s.id=f.scan_id"
            query += " INNER JOIN planet_dump AS p1 ON s.pid=p1.id"
            query += (
                " INNER JOIN planet_dump AS p2 ON p1.tick=p2.tick AND f.owner_id=p2.id"
            )
            query += " WHERE p1.tick=(SELECT max_tick(%s::smallint)) AND p1.round=%s AND s.rand_id=%s"
            self.cursor.execute(query, (irc_msg.round, irc_msg.round, rand_id,))
            if self.cursor.rowcount > 0:
                results = self.cursor.fetchall()
                s = results[0]
                irc_msg.reply(self.reply_jgp(link,
                                             rand_id,
                                             s["targ_x"],
                                             s["targ_y"],
                                             s["targ_z"],
                                             results,
                                             s["tick"]))
            else:
                irc_msg.reply("No JGP scans available with ID %s" %(rand_id,))
                return 0
        return 1

    def reply_jgp(self, link, rand_id, x, y, z, results, tick):
        if not link:
            prev = []
            for s in results:
                prev.append(
                    "(%s:%s:%s %s | %s %s %s)"
                    % (
                        s["x"],
                        s["y"],
                        s["z"],
                        s["fleet_name"],
                        s["fleet_size"],
                        s["mission"],
                        s["eta"],
                    )
                )

            reply = "JGP scan on %s:%s:%s (id: %s, pt: %s) " % (x, y, z, rand_id, tick,)
            reply += " | ".join(prev)
            if len(reply) > 450:
                link = True
        if link:
            reply = "JGP scan on %s:%s:%s (id: %s, pt: %s) " % (x, y, z, rand_id, tick)
            reply += "http://game.planetarion.com/showscan.pl?scan_id=%s" % (
                rand_id,
            )
        return reply
