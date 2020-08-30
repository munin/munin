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

import re
from munin import loadable


class banzai(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(.*)")
        self.usage = self.__class__.__name__ + " [shout]"

    def execute(self, user, access, irc_msg):

        param_match = self.paramre.search(irc_msg.command_parameters)
        if not param_match:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        stuff = param_match.group(1)
        lemmings = self.fetch_lemmings(irc_msg.round)
        hilights = []

        for l in lemmings:
            if l["alias_nick"]:
                hilights.append(f"@{l['pnick']} / @{l['alias_nick']}")
            else:
                hilights.append(f"@{l['pnick']}")
        commander = irc_msg.user or irc_msg.nick
        reply = f"{commander}"
        if stuff:
            reply += f" shouts '{stuff}' and"
        reply += " calls upon you to die for your emperor, " + ", ".join(hilights)

        irc_msg.reply(reply)
        return 1

    def fetch_lemmings(self, rnd):
        query = "SELECT u.pnick, u.alias_nick FROM user_list AS u"
        query += " INNER JOIN round_user_pref AS rup"
        query += " ON u.id = rup.user_id AND rup.round=%s"
        query += " WHERE u.userlevel >= 100 AND rup.lemming"
        self.cursor.execute(query, (rnd,))
        return self.cursor.fetchall()
