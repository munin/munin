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

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08


import re
from munin import loadable


class bumchums(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 50)
        self.paramre = re.compile(r"^\s+(.+)\s+(\d+)\s*$")
        self.usage = self.__class__.__name__ + " <alliance> <number>"
        self.helptext = ["Pies"]

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

        alliance = m.group(1)
        bums = m.group(2) or 1

        a = loadable.alliance(name=alliance)

        if not a.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply("No alliance matching '%s' found" % (alliance,))
            return 1

        query = "SELECT x,y,count(*) AS bums FROM planet_dump AS t1"
        query += " INNER JOIN intel AS t2 ON t1.id=t2.pid"
        query += " LEFT JOIN alliance_canon AS t3 ON t2.alliance_id=t3.id"
        query += " WHERE t1.tick=(SELECT max_tick(%s::smallint))"
        query += " AND t3.name ilike %s"
        query += " AND t1.round=%s"
        query += " GROUP BY x,y"
        query += " HAVING count(*) >= %s"
        query += " ORDER BY bums DESC, x ASC, y ASC"

        # do stuff here

        self.cursor.execute(query, (irc_msg.round, a.name, irc_msg.round, bums,))

        reply = ""
        if self.cursor.rowcount < 1:
            reply += "No galaxies with at least %s bumchums from %s" % (bums, a.name)
        else:
            prev = []
            for b in self.cursor.fetchall():
                prev.append("%s:%s (%s)" % (b["x"], b["y"], b["bums"]))
            reply += "Galaxies with at least %s bums from %s: " % (
                bums,
                a.name,
            ) + " | ".join(prev)

        irc_msg.reply(reply)

        return 1
