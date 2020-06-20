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


class yourmum(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(\S+)?")
        self.usage = self.__class__.__name__ + " [pnick]"
        self.helptext = None

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        search = m.group(1)
        if search:
            u = self.load_user_from_pnick(search, irc_msg.round)
            if not u:
                irc_msg.reply("No member found matching %s." % (search,))
                return
        else:
            u = self.load_user(irc_msg.user, irc_msg)
            if not u:
                return

        self.show_mums_for_user(u, irc_msg)
        return 1

    def show_mums_for_user(self, u, irc_msg):
        most_given = self.get_ten_biggest_mums(u.id)
        reply = "%s is %s carebears fat. These people care most for %s: " % (
            u.pnick,
            u.carebears,
            u.pnick,
        )
        reply += ", ".join(["%s (%s)" % (x["giver"], x["cookies"]) for x in most_given])
        irc_msg.reply(reply)

    def get_ten_biggest_mums(self, receiver):
        query = "SELECT pnick AS giver,sum(howmany) AS cookies"
        query += " FROM cookie_log AS t1"
        query += " INNER JOIN user_list AS t2 ON t1.giver=t2.id"
        query += " WHERE receiver = %s"
        query += " GROUP BY pnick"
        query += " ORDER BY sum(howmany) DESC"
        query += " LIMIT 10"
        self.cursor.execute(query, (receiver,))
        return self.cursor.fetchall()
