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
import munin.loadable as loadable


class cookiemonsters(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*")
        self.usage = self.__class__.__name__
        self.helptext = [
            "List members who have received most carebears and who have given"
            " away the most cookies."
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        irc_msg.reply("Biggest feeders: %s | Fattest gainers: %s" % (
            self.feeders(),
            self.gainers(),
        ))
        return 1

    def gainers(self):
        self.cursor.execute("""
        SELECT pnick, carebears AS cookies
        FROM user_list
        WHERE userlevel >= 100
        ORDER BY cookies DESC
        LIMIT 5;
        """)
        return self.format(self.cursor.fetchall())

    def feeders(self):
        self.cursor.execute("""
        SELECT pnick, sum(howmany) AS cookies
        FROM       cookie_log AS l
        INNER JOIN user_list  AS u ON l.giver=u.id
        WHERE u.userlevel >= 100
        GROUP BY u.pnick
        ORDER BY sum(l.howmany) DESC
        LIMIT 5;
        """)
        return self.format(self.cursor.fetchall())

    def format(self, results):
        return ', '.join([
            "%s (%s)" % (
                row['pnick'],
                row['cookies'],
            )
            for row in results
        ])
