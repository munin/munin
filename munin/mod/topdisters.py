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

import re

from munin import loadable


class topdisters(loadable.loadable):
    """
    Show the planets with the most distorters in the universe.
    """

    def __init__(self, cursor):
        super().__init__(cursor, 50)
        self.paramre = re.compile(r"^\s*")
        self.usage = self.__class__.__name__
        self.helptext = [
            "Show the planets with the most distorters in the universe"
        ]

    def execute(self, user, access, irc_msg):
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            return self.reply_usage(irc_msg)

        limit = 10
        query = (
            "SELECT * "
            "FROM ("
            "    SELECT x, y, z, s.tick AS scan_tick, wave_distorter, "
            "           rank() OVER (PARTITION BY s.pid ORDER BY s.id DESC) AS rank "
            "    FROM scan AS s "
            "    INNER JOIN development AS d ON d.scan_id = s.id "
            "    INNER JOIN planet_dump AS p ON s.round = p.round AND p.id = s.pid "
            "    WHERE p.round = %s "
            "    AND p.tick = (SELECT max_tick(%s::smallint)) "
            "    ORDER BY wave_distorter DESC"
            ") AS scans "
            "WHERE rank = 1 "
            "LIMIT %s"
        )
        self.cursor.execute(query, (irc_msg.round, irc_msg.round, limit,))
        entries = [self.format_result(s) for s in self.cursor.fetchall()]
        irc_msg.reply('Top dist whores: %s' % (' | '.join(entries),))
        return 1

    def reply_usage(self, irc_msg):
        irc_msg.reply("Usage: %s" % (self.usage,))
        return 0

    def format_result(self, s):
        return "%s:%s:%s (%s at pt%s)" % (s['x'], s['y'], s['z'], s['wave_distorter'], s['scan_tick'],)
