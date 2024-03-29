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


class exp(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(\d+)[. :-](\d+)[. :-](\d+)(?:\s+(\d+))?")
        self.usage = self.__class__.__name__ + " <coords> [tick]"
        self.helptext = [
            "Shows experience gain during the last 15 ticks or experience gain "
            "during one specific tick."
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        tick = m.group(4)

        p = loadable.planet(x=x, y=y, z=z)
        if not p.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply("No planet matching '%s:%s:%s' found" % (x, y, z))
            return 1

        reply = ""

        if tick:
            query = "SELECT t1.xp,t1.xp-t2.xp AS vdiff,t1.size-t2.size AS sdiff"
            query += " FROM planet_dump AS t1"
            query += " INNER JOIN planet_dump AS t2"
            query += " ON t1.id=t2.id AND t1.tick-1=t2.tick"
            query += " WHERE t1.tick=%s"
            query += " AND t1.id=%s"
            self.cursor.execute(query, (tick, p.id,))
            if self.cursor.rowcount < 1:
                reply += "No data for %s:%s:%s on tick %s" % (p.x, p.y, p.z, tick)
            else:
                x = self.cursor.fetchone()

                reply += "Experience on pt%s for %s:%s:%s: " % (tick, p.x, p.y, p.z)
                reply += "xp: %s (%s%s) " % (
                    x["xp"],
                    ["+", "-"][x["vdiff"] < 0],
                    abs(x["vdiff"]),
                )
                if x["sdiff"] != 0:
                    reply += "roids: %s%s" % (
                        ["+", "-"][x["sdiff"] < 0],
                        abs(x["sdiff"]),
                    )
        else:
            query = "SELECT t1.tick,t1.xp,t1.xp-t2.xp AS vdiff,t1.size-t2.size AS sdiff"
            query += " FROM planet_dump AS t1"
            query += " INNER JOIN planet_dump AS t2"
            query += " ON t1.id=t2.id AND t1.tick-1=t2.tick"
            query += " WHERE t1.tick>(SELECT max_tick(%s::smallint)-16)"
            query += " AND t1.id=%s"
            query += " ORDER BY t1.tick ASC"
            self.cursor.execute(query, (irc_msg.round, p.id,))
            if self.cursor.rowcount < 1:
                reply += "No data for %s:%s:%s" % (p.x, p.y, p.z)
            else:
                results = self.cursor.fetchall()

                reply += "Experience in the last 15 ticks on %s:%s:%s: " % (
                    p.x,
                    p.y,
                    p.z,
                )

                info = [
                    "pt%s %s (%s%s)"
                    % (
                        x["tick"],
                        self.format_value(x["xp"] * 100),
                        ["+", "-"][x["vdiff"] < 0],
                        self.format_value(abs(x["vdiff"] * 100)),
                    )
                    + [
                        " roids:" + ["+", "-"][x["sdiff"] < 0] + str(abs(x["sdiff"])),
                        "",
                    ][x["sdiff"] == 0]
                    for x in results
                ]

                reply += str.join(" | ", info)
        irc_msg.reply(reply)
        return 1
