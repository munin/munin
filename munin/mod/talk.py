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

# Nothing ascendancy/jester specific in this module.
# qebab, 24/6/08.

import re
from munin import loadable


class talk(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(\S+)\s+(.*)")
        self.usage = self.__class__.__name__ + " <target> <stuff>"

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        targ = m.group(1)
        stuff = m.group(2)
        if access < self.level:
            irc_msg.reply("You do not have enough access to send raw commands")
            return 0

        irc_msg.client.privmsg(targ, stuff)
        return 1
