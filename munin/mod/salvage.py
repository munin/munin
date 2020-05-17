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

import re
from munin import loadable
from functools import reduce


class salvage(loadable.loadable):
    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 1)
        self.paramre = re.compile(r"\s*(?:(\d+)[.-:\s](\d+)[.-:\s](\d+))?\s*$")
        self.usage = self.__class__.__name__ + " [coords]"

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0

        m = self.paramre.match(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        planet = None

        if m.lastindex == 3 and m.group(1) and m.group(2) and m.group(3):
            planet = loadable.planet(x=m.group(1), y=m.group(2), z=m.group(3))
            if not planet.load_most_recent(self.cursor, irc_msg.round):
                irc_msg.reply(
                    "%s:%s:%s is not a valid planet" % (planet.x, planet.y, planet.z)
                )
                return 1
        else:
            u = loadable.user(pnick=irc_msg.user)
            if not u.load_from_db(self.cursor, irc_msg.round):
                irc_msg.reply(
                    "You must be registered to use the automatic "
                    + self.__class__.__name__
                    + " command (log in with P and set mode +x, then make sure your planet is set with the pref command)"
                )
                return 1
            if u.planet_id:
                planet = u.planet
            else:
                irc_msg.reply(
                    "Usage: %s (make sure your planet is set with the pref command)"
                    % (self.usage,)
                )
                return 1

        if not planet:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        query = "SELECT score"
        query += " FROM planet_dump"
        query += " WHERE tick=(SELECT max_tick(%s::smallint)) AND round=%s"
        query += " ORDER BY score_rank ASC"
        query += " LIMIT 20"
        self.cursor.execute(query, (irc_msg.round, irc_msg.round,))
        if self.cursor.rowcount < 1:
            irc_msg.reply("Error retrieving score of top 20 planets from database")
        top20_average_score = reduce(
            lambda s, p: s + float(p["score"]) / 20.0, self.cursor.dictfetchall(), 0.0
        )

        score_modifier = 0.5 * (1.0 - float(planet.score) / top20_average_score)
        race_bonus = self.config.getfloat("Planetarion", planet.race + "_salvage_bonus")
        salvage_rate = 0.3 * (1.0 + race_bonus) * (1.0 + score_modifier)
        reply = "%s:%s:%s (%s|%s) gets a defense salvage rate of %2.1f%%" % (
            planet.x,
            planet.y,
            planet.z,
            self.format_value(planet.value * 100),
            self.format_value(planet.score * 100),
            100 * salvage_rate,
        )
        irc_msg.reply(reply)
        return 1
