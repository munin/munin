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

# This module has nothing ascendancy specific as far as I can tell.
# qebab, 24/6/08.

import re
from munin import loadable


class spam(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(\S+)\s*$")
        self.usage = self.__class__.__name__ + " <alliance>"

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        params = m.group(1)

        args = (
            irc_msg.round,
            irc_msg.round,
            "%" + params + "%",
        )
        query = "SELECT t1.x AS x,t1.y AS y,t1.z AS z,t1.size AS size,t1.score AS score,t1.value AS value,t1.race AS race,t6.name AS alliance,t2.nick AS nick,t2.reportchan AS reportchan,t2.comment AS comment"
        query += " FROM planet_dump AS t1 INNER JOIN planet_canon AS t3 ON t1.id=t3.id"
        query += " INNER JOIN intel AS t2 ON t3.id=t2.pid"
        query += " LEFT JOIN alliance_canon AS t6 ON t2.alliance_id=t6.id"
        query += " WHERE t1.tick=(SELECT max_tick(%s::smallint)) AND t1.round=%s AND (t6.name ILIKE %s) ORDER BY x,y,z"
        self.cursor.execute(query, args)

        planets = self.cursor.fetchall()
        if not len(planets):
            reply = "No planets in intel matching alliance: %s" % (params,)
            irc_msg.reply(reply)
            return 1

        printable = ["%s:%s:%s" % (d["x"], d["y"], d["z"]) for d in planets]
        reply = "Spam on alliance %s - %s" % (
            planets[0]["alliance"],
            str.join(", ", printable)
        )
        irc_msg.reply(reply)

        return 1
