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

# No alliance specific things found in this module.
# qebab, 24/6/08.

import re
from munin import loadable


class lookup(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(.*)")
        self.usage = self.__class__.__name__ + " [x:y[:z]|alliancename]"

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m or not m.group(1):
            u = loadable.user(pnick=irc_msg.user)
            if not u.load_from_db(self.cursor, irc_msg.round):
                irc_msg.reply(
                    "You must be registered to use the automatic "
                    + self.__class__.__name__
                    + " command (log in with Q and set mode +x, then make sure you've set your planet with the pref command)"
                )
                return 1
            if u.planet:
                irc_msg.reply(str(u.planet))
            else:
                irc_msg.reply("Usage: %s" % (self.usage,))
            return 1
        param = m.group(1)
        m = self.coordre.search(param)
        if m:
            x = m.group(1)
            y = m.group(2)
            z = m.group(4)

            if z:
                p = loadable.planet(x=x, y=y, z=z)
                if not p.load_most_recent(self.cursor, irc_msg.round):
                    irc_msg.reply("No planet matching '%s' found" % (param,))
                    return 1
                irc_msg.reply(str(p))
                return 1
            else:
                g = loadable.galaxy(x=x, y=y)
                if not g.load_most_recent(self.cursor, irc_msg.round):
                    irc_msg.reply("No galaxy matching '%s' found" % (param,))
                    return 1
                irc_msg.reply(str(g))
                return 1

        # check if this is an alliance
        a = loadable.alliance(name=param.strip())
        if a.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply(str(a))
            return
        u = self.load_user_from_pnick(param.strip(), irc_msg.round)
        if u and irc_msg.access >= 100:
            if u.planet:
                irc_msg.reply(str(u.planet))
            else:
                irc_msg.reply(
                    "User %s has not entered their planet details" % (u.pnick,)
                )
            return

        irc_msg.reply("No alliance or user matching '%s' found" % (param,))
        return
