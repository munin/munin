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
# I lied. Removed alliance specific things.
# qebab, 24/6/08.

import re
from munin import loadable


class bigadicks(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*")
        self.usage = self.__class__.__name__
        self.helptext = [
            "Find the alliances with the largest score gains over the last 72"
            " ticks"
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        query = """
        SELECT *, rank() OVER (ORDER BY activity DESC) AS activity_rank
        FROM (
            SELECT t1.name, t1.score-t72.score AS activity
            FROM       alliance_dump AS t1
            INNER JOIN alliance_dump AS t72 ON t1.id = t72.id AND t1.tick - 72 = t72.tick
            WHERE t1.tick  = (SELECT max_tick(%s::smallint))
            AND   t1.round = %s
            ORDER BY activity DESC
            LIMIT 5
        ) res
        """

        self.cursor.execute(query, (
            irc_msg.round,
            irc_msg.round,
        ))

        if self.cursor.rowcount < 1:
            self.cursor.execute("SELECT max_tick(%s::smallint)", (irc_msg.round,))
            if self.cursor.fetchone()['max_tick'] < 73:
                irc_msg.reply("There is no penis before tick 73")
            else:
                irc_msg.reply("The penis isn't small! IT'S CLOAKED!")
            return 1

        adicks = [
            "%d:%s (%s)" % (
                b["activity_rank"],
                b["name"],
                self.format_value(b["activity"] * 100),
            )
            for b in self.cursor.fetchall()
        ]
        irc_msg.reply("Big alliance dicks: %s" % (
            ", ".join(adicks),
        ))
        return 1
