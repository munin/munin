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

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08

import re
from munin import loadable


class cost(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(\d+(?:\.\d+)?[TtBbMmKk]?)\s+(\S+)(?:\s+(\S+))?")
        self.usage = self.__class__.__name__ + " <number> <shipname> [government]"

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        ship_number = self.human_readable_number_to_integer(m.group(1))
        ship_name = m.group(2)

        gov_name = ""
        prod_bonus = 1
        if m.group(3):
            lower_gov_name = m.group(3).lower()
            if lower_gov_name in "totalitarianism":
                prod_bonus = 1 - float(
                    self.config.get("Planetarion", "totalitarianism_cost_reduction")
                )
                gov_name = "Totalitarianism"
            elif lower_gov_name in "democracy":
                prod_bonus = 1 - float(
                    self.config.get("Planetarion", "democracy_cost_reduction")
                )
                gov_name = "Democracy"

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        ship = self.get_ship_from_db(ship_name, irc_msg.round)
        if not ship:
            irc_msg.reply("%s is not a ship" % (ship_name))
            return 0

        metal = int(ship["metal"] * prod_bonus) * ship_number
        crystal = int(ship["crystal"] * prod_bonus) * ship_number
        eonium = int(ship["eonium"] * prod_bonus) * ship_number
        resource_value = (metal + crystal + eonium) / 150
        ship_value = round((ship["total_cost"] * ship_number) / 100)
        reply = "Buying %s %s will cost %s metal, %s crystal and %s eonium" % (
            ship_number,
            ship["name"],
            metal,
            crystal,
            eonium,
        )

        if prod_bonus != 1:
            reply += " as %s" % (gov_name)

        reply += ". This gives %s ship value (%s increase)" % (
            ship_value,
            round(ship_value - resource_value),
        )

        irc_msg.reply(reply)

        return 1
