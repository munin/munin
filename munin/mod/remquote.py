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


class remquote(loadable.loadable):
    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 100)
        self.paramre = re.compile(r"^\s+(.*)$")
        self.usage = self.__class__.__name__ + " <quote to remove>"

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0

        m = self.paramre.search(m.group(1))

        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        params = m.group(1)
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        args = (params,)
        query = "SELECT quote FROM quote WHERE quote = %s"
        self.cursor.execute(query, args)
        if self.cursor.rowcount == 1:
            slogan = self.cursor.dictfetchone()['quote']
            args = (params,)
            query = "DELETE FROM quote WHERE quote=%s"
            self.cursor.execute(query, args)
            reply = "Removed: '%s'" % (slogan,)
            irc_msg.reply(reply)
            return 1

        args = ("%" + params + "%",)
        query = "SELECT quote FROM quote WHERE quote ILIKE %s"
        self.cursor.execute(query, args)
        results = self.cursor.rowcount

        if results > 1:
            reply = "There were %d quotes matching your search, I can only be bothered to delete one quote at a time you demanding fuckwit" % (
                results,)
        elif results == 0:
            reply = "No quote matching '%s'" % (params,)
        else:
            slogan = self.cursor.dictfetchone()['quote']
            args = (slogan,)
            query = "DELETE FROM quote WHERE quote = %s"
            self.cursor.execute(query, args)
            print self.cursor.rowcount
            reply = "Removed: '%s'" % (slogan,)

        irc_msg.reply(reply)

        # do stuff here

        return 1
