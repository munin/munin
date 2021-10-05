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


class getanewdaddy(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(\S+)")
        self.usage = self.__class__.__name__ + " <pnick>"
        self.helptext = [
            'This command is used when you no longer wish to be sponsor for a person. Their access to #%s will be removed and their Munin access will be lowered to "galmate" level.'
            % self.config.get("Auth", "home"),
            "Anyone is free to sponsor the person back under the usual conditions. This isn't a kick and it's not final.",
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        voter = loadable.user(pnick=irc_msg.user)
        if not voter.load_from_db(self.cursor, irc_msg.round):
            irc_msg.reply(
                "You must be registered to use the "
                + self.__class__.__name__
                + " command (log in with Q and set mode +x)"
            )
            return 1

        idiot = loadable.user(pnick=m.group(1))
        if not idiot.load_from_db(self.cursor, irc_msg.round):
            irc_msg.reply("That idiot doesn't exist")
            return 1

        if (
            access < 1000
            and idiot.sponsor.lower() != voter.pnick.lower()
            and idiot.pnick.lower() != voter.pnick.lower()
        ):
            reply = "You are not %s's sponsor" % (idiot.pnick,)
            irc_msg.reply(reply)
            return 1

        query = "UPDATE user_list SET userlevel = 1 WHERE id = %s"
        self.cursor.execute(query, (idiot.id,))
        irc_msg.client.privmsg(
            "Q",
            "removeuser #%s %s"
            % (
                self.config.get("Auth", "home"),
                idiot.pnick,
            ),
        )
        irc_msg.client.privmsg(
            "Q",
            "permban #%s *!*@%s.users.quakenet.org Your sponsor doesn't like you anymore"
            % (
                self.config.get("Auth", "home"),
                idiot.pnick,
            ),
        )

        if idiot.sponsor != voter.pnick:
            reply = (
                "%s has been reduced to level 1 and removed from the channel. %s is no longer %s's sponsor. If anyone else would like to sponsor that person back, they may."
                % (idiot.pnick, idiot.sponsor, idiot.pnick)
            )
        else:
            reply = (
                "%s has been reduced to level 1 and removed from the channel. You are no longer %s's sponsor. If anyone else would like to sponsor that person back, they may."
                % (idiot.pnick, idiot.pnick)
            )
        irc_msg.reply(reply)
        return 1
