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


class tickinfo(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*")
        self.usage = self.__class__.__name__ + ""
        self.helptext = ['Shows information about the latest tick.']

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

        query = "SELECT tick, age(now(), updates.timestamp) AS tick_age FROM updates WHERE round = %s ORDER BY tick DESC LIMIT 1"
        self.cursor.execute(query, (irc_msg.round,))
        reply = ""
        if self.cursor.rowcount < 1:
            reply = "Don't be stupid, that doesn't exist."
        else:
            res = self.cursor.dictfetchone()
            reply = "My current tick information is for pt%s, which I retrieved %s ago" % (res['tick'], res['tick_age'])
        irc_msg.reply(reply)

        return 1
