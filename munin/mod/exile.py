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


class exile(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^(.*)")
        self.usage = self.__class__.__name__ + ""
        self.helptext = ["Show the galaxies eligible for exiles."]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        reply = ""

        query = "SELECT planets,count(*) AS count"
        query += " FROM (SELECT x AS x,y AS y,count(*) AS planets FROM planet_dump"
        query += "       WHERE tick = (SELECT max_tick(%s::smallint)) AND round = %s AND x < 200 AND NOT (x = 1 AND y = 1)"
        query += "       GROUP BY x,y ORDER BY count(*) DESC) AS foo"
        query += " GROUP BY planets ORDER BY planets ASC"

        self.cursor.execute(query, (irc_msg.round, irc_msg.round,))
        if self.cursor.rowcount < 1:
            reply = "There is no spoon"
        else:
            res = self.cursor.fetchall()
            gals = 0
            bracket = 0
            base_bracket_gals = 0
            max_planets = 0

            for r in res:
                gals += r["count"]
            bracket = int(gals * 0.2)
            for r in res:
                bracket -= r["count"]
                if bracket < 0:
                    rest_gals = bracket + r["count"]
                    total_rest_gals = r["count"]
                    rest_planets = r["planets"]
                    if max_planets == 0:
                        max_planets = r["planets"] - 1
                    break
                max_planets = r["planets"]
                base_bracket_gals += r["count"]

            reply = (
                "Total galaxies: %s | %s galaxies with a maximum of %s planets guaranteed to be in the exile bracket"
                % (gals, base_bracket_gals, max_planets)
            )

            if base_bracket_gals > 0:
                # >0 galaxies are guaranteed to be in the bracket. List them.
                query = "SELECT x, y FROM ("
                query += "     SELECT x AS x,y AS y,count(*) AS planets"
                query += "     FROM planet_dump"
                query += "     WHERE tick = (SELECT max_tick(%s::smallint))"
                query += "     AND round = %s"
                query += "     AND x < 200"
                query += "     AND NOT (x = 1 AND y = 1)"
                query += "     GROUP BY x,y"
                query += "     ORDER BY count(*) DESC"
                query += " ) AS foo"
                query += " WHERE planets <= %s"
                query += " ORDER BY x ASC, y ASC"
                self.cursor.execute(query, (irc_msg.round, irc_msg.round, max_planets,))
                eligible = "Whoops"
                if self.cursor.rowcount > 0:
                    eligible = ", ".join(
                        ["%s:%s" % (x["x"], x["y"]) for x in self.cursor.fetchall()]
                    )
                reply += ": %s" % (eligible)
            reply += " | Also in the bracket: %s of %s galaxies with %s planets." % (
                rest_gals,
                total_rest_gals,
                rest_planets,
            )

        irc_msg.reply(reply)

        return 1
