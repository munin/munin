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


class conscript(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(\S+)")
        self.usage = self.__class__.__name__ + " <pnick>"
        self.helptext = [
            "Conscripts a user into the emperor's lemming army. They will be called upon to sacrifice themselves with !banzai."
        ]

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        search = m.group(1)
        conscriptor = irc_msg.user or irc_msg.nick

        if search.lower() == self.config.get("Connection", "nick").lower():
            irc_msg.reply(
                "I watch, I wait, I do not involve myself in the affairs of mortals"
            )
            return 1
        if access < self.level:
            irc_msg.reply("You do not have enough access to conscript anyone")
            return 0

        minimum_userlevel = 100

        r = self.load_user_from_pnick(
            search, irc_msg.round, minimum_userlevel=minimum_userlevel
        )

        reply = ""

        if not r or r.userlevel < minimum_userlevel:
            reply += (
                "There's no member matching '%s' so I can't very well conscript them, can I?"
                % (search,)
            )
            return 1

        query = "INSERT INTO round_user_pref (user_id,round,lemming) VALUES (%s,%s,%s)"
        query += " ON CONFLICT (user_id,round) DO"
        query += " UPDATE SET lemming=EXCLUDED.lemming"
        args = (
            r.id,
            irc_msg.round,
            "yes",
        )
        if r.pnick == irc_msg.user:
            reply += f"{r.pnick} is too lazy to use the pref-command, but don't worry, their fate in the emperor's lemming army has been sealed."
        else:
            reply += (
                f"{conscriptor} has conscripted {r.pnick} to the emperor's lemming army"
            )
        self.cursor.execute(query, args)
        irc_msg.client.privmsg("#%s" % (self.config.get("Auth", "home"),), reply)

        return 1
