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


class orphans(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*")
        self.usage = self.__class__.__name__ + ""
        self.helptext = [
            "Lists all members whose sponsors are no longer members. Use !adopt to someone's sponsor."
        ]

    def execute(self, user, access, irc_msg):
        m = self.commandre.search(irc_msg.command)
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
        query = "SELECT t1.pnick AS pnick FROM user_list t1"
        query += " INNER JOIN user_list t2 ON t1.sponsor ilike t2.pnick"
        query += " WHERE t1.userlevel >= 100 AND t2.userlevel < 100"

        self.cursor.execute(query)
        reply = ""
        if self.cursor.rowcount < 1:
            reply = "There are no orphans. KILL A PARENT NOW."
        else:
            reply = "The following members are orphans: "
            res = self.cursor.fetchall()
            reply += ", ".join([x["pnick"] for x in res])

        irc_msg.reply(reply)

        return 1
