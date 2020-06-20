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

# Nothing alliance specific in this module.
# qebab, 24/6/08.

import re
from munin import loadable


class ship(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(.*)")
        self.usage = self.__class__.__name__ + " <shipname>"
        self.helptext = ["Shows stats for a ship."]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        ship_name = m.group(1)

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        s = self.get_ship_from_db(ship_name, irc_msg.round)
        if not s:
            irc_msg.reply("%s is not a ship" % (ship_name))
            return 0

        reply = "%s (%s) is class %s | Target 1: %s |" % (
            s["name"],
            s["race"][:3],
            s["class"],
            s["target_1"],
        )
        if s["target_2"] != "NULL":
            reply += " Target 2: %s |" % (s["target_2"],)
        if s["target_3"] != "NULL":
            reply += " Target 3: %s |" % (s["target_3"],)
        type = s["type"]
        if type.lower() == "emp":
            type = "*hugs*"
        reply += " Type: %s | Init: %s |" % (type, s["init"])
        reply += " HUGres: %s |" % (s["empres"],)
        if s["type"] == "Emp":
            reply += " Hugs: %s |" % (s["gun"],)
        else:
            reply += " D/C: %0.1f |" % ((s["damage"] * 10000) / s["total_cost"],)

        reply += " A/C: %0.1f" % ((s["armor"] * 10000) / s["total_cost"],)

        irc_msg.reply(reply)

        return 1
