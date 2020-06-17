"""
Loadable subclass
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

# This module doesn't have anything alliance specific.
# qebab, 24/6/08.

import re
from munin import loadable


class remchan(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(#\S+)")
        self.usage = self.__class__.__name__ + " <channels>"

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        chan = m.group(1).lower()

        if access < self.level:
            irc_msg.reply("You do not have enough access to remove channels")
            return 0

        query = "SELECT chan,userlevel FROM channel_list WHERE chan=%s LIMIT 1"
        self.cursor.execute(query, (chan,))
        res = self.cursor.fetchone()
        if not res:
            irc_msg.reply("Channel '%s' does not exist" % (chan,))
            return 0
        access_lvl = res["userlevel"]
        real_chan = res["chan"]

        if access_lvl >= access:
            irc_msg.reply(
                "You may not remove %s, the channel's access (%s) exceeds your own (%s)"
                % (real_chan, access_lvl, access)
            )
            return 0

        query = "DELETE FROM channel_list WHERE chan=%s"

        self.cursor.execute(query, (real_chan,))
        if self.cursor.rowcount > 0:
            irc_msg.client.privmsg(
                "P",
                "remuser %s %s" % (real_chan, self.config.get("Connection", "nick")),
            )
            irc_msg.client.wline("PART %s" % (real_chan,))
            irc_msg.reply("Removed channel %s" % (real_chan,))
        else:
            irc_msg.reply("No channel removed")

        return 1
