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


class range(loadable.loadable):
    def __init__(self, client, conn, cursor):
        loadable.loadable.__init__(self, client, conn, cursor, 50)
        self.commandre = re.compile(r"^" + self.__class__.__name__ + "(.*)")
        self.paramre = re.compile(r"^\s*(.*)")
        self.idre = re.compile(r"(\d{1,9})")
        self.usage = self.__class__.__name__ + ""
        self.helptext = None

    def execute(self, nick, username, host, target, prefix, command, user, access):
        m = self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(
                prefix,
                nick,
                target,
                "You do not have enough access to use this command",
            )
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            self.client.reply(prefix, nick, target, "Usage: %s" % (self.usage,))
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
            if not p.load_most_recent(self.conn, self.client, self.cursor):
                self.client.reply(
                    prefix, nick, target, "No planet matching '%s' found" % (param,)
                )
                return 1

            query = "SELECT t3.name AS name, floor(max(t1.amount)::float/1.2) AS min,floor(min(t1.amount)::float/0.8) AS max"
            query += " FROM unit AS t1"
            query += " INNER JOIN ship AS t3"
            query += " ON t1.ship_id=t3.id"
            query += " INNER JOIN scan AS t2"
            query += " ON t1.scan_id=t2.id"
            query += " WHERE tick > (SELECT max_tick()-48) AND t2.pid=%s"
            query += " GROUP BY name"
            self.cursor.execute(query, (p.id,))

            if self.cursor.rowcount < 1:
                reply += (
                    "No unit scans available on %s:%s:%s from the last 48 ticks"
                    % (p.x, p.y, p.z)
                )

            else:
                reply += "Unit ranges for %s:%s:%s from data the last 48 ticks: " % (
                    p.x,
                    p.y,
                    p.z,
                )

                prev = []
                for s in self.cursor.fetchall():
                    prev.append("%s %d-%d" % (s["name"], s["min"], s["max"]))

                reply += string.join(prev, " | ")

        self.client.reply(prefix, nick, target, reply)
        return 1
