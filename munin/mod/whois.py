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

# Nothing ascendancy/jester specific found here.
# qebab, 24/6/08.

import re
from munin import loadable


class whois(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(\S+)")
        self.usage = self.__class__.__name__ + ""
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

        if search.lower() == self.config.get("Connection", "nick").lower():
            irc_msg.reply("I am Munin. Hear me roar.")
            return 1

        minimum_userlevel = 100
        r = self.load_user_from_pnick(
            search, irc_msg.round, minimum_userlevel=minimum_userlevel
        )

        reply = ""

        if not r or r.userlevel < minimum_userlevel:
            reply += "No members matching '%s'" % (search,)
        else:
            if r.pnick == irc_msg.user:
                reply += "You are %s. You are also known as %s. Your sponsor is %s. Your Munin number is %s. You have %d %s. You are%s a lemming"
            else:
                reply += "Information about %s: They are also known as %s. Their sponsor is %s. Their Munin number is %s. They have %d %s. They are%s a lemming"
            reply = reply % (
                r.pnick,
                r.alias_nick,
                r.sponsor,
                self.munin_number_to_output(r, irc_msg.round),
                r.carebears,
                self.pluralize(r.carebears, "carebear"),
                "" if r.lemming else " not",
            )

        irc_msg.reply(reply)
        return 1

    def munin_number_to_output(self, u, round):
        number = u.munin_number(self.cursor, self.config, round)
        return number or "a kabajillion"
