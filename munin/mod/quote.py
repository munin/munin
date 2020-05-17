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


class quote(loadable.loadable):
    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 1)
        self.paramre = re.compile(r"^\s+(.*)$")
        self.usage = self.__class__.__name__ + ""

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0

        m = self.paramre.search(m.group(1))
        params = None
        if m:
            params = m.group(1)

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        args = ()
        query = "SELECT quote FROM quote WHERE 1=1"

        if params:
            query += " AND quote ILIKE %s"
            args += ("%" + params.replace("*", "%") + "%",)

        query += " ORDER BY RANDOM()"
        self.cursor.execute(query, args)

        reply = ""
        if self.cursor.rowcount == 0:
            reply += "No quotes matching '%s'" % (params,)
        else:
            res = self.cursor.fetchone()
            reply += "%s" % (res["quote"],)
            if self.cursor.rowcount > 1 and params:
                reply += " (%d more quotes match this search)" % (
                    self.cursor.rowcount - 1
                )

        irc_msg.reply(reply)

        # do stuff here

        return 1
