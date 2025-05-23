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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

# Nothing ascendancy specific in this module.
# qebab, 24/6/08.

import re
import math
from munin import loadable


class stop(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(\d+(?:\.\d+)?[TtBbMmKk]?)\s+(\S+)(\s+(t1|t2|t3))?")
        self.usage = self.__class__.__name__ + " <number> <target> [t1|t2|t3]"

    def execute(self, user, access, irc_msg):
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            if re.search(r"\s*hammertime", irc_msg.command_parameters, re.I):
                irc_msg.reply("Can't touch this!")
                return 1
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        ship_number = self.human_readable_number_to_integer(m.group(1))
        bogey = m.group(2)
        user_target = m.group(4)

        target_number = None
        if not user_target or user_target == "t1":
            target_number = "target_1"
            user_target = "t1"
        elif user_target == "t2":
            target_number = "target_2"
        elif user_target == "t3":
            target_number = "target_3"

        efficiency = float(self.config.get("Planetarion", "%s_eff" % (user_target,)))

        ship = self.get_ship_from_db(bogey, irc_msg.round)
        if not ship:
            if "asteroids".rfind(bogey) > -1:
                ship = {
                    "name": "Asteroid",
                    "class": "Roids",
                    "armor": 50,
                    "total_cost": 20000,
                }
            elif "structures".rfind(bogey) > -1:
                ship = {
                    "name": "Structure",
                    "class": "Struct",
                    "armor": 500,
                    "total_cost": 20000,
                }
            elif "resources".rfind(bogey) > -1:
                ship = {
                    "name": "Resources",
                    "class": "Rs",
                    "armor": 0.02,
                    "total_cost": 1,
                }
            else:
                irc_msg.reply("%s is not a ship" % (bogey))
                return 0
        total_armor = ship["armor"] * ship_number

        query = (
            "SELECT * FROM ship WHERE " + target_number + "=%s AND round=%s ORDER BY id"
        )
        self.cursor.execute(
            query,
            (
                ship["class"],
                irc_msg.round,
            ),
        )
        attackers = self.cursor.fetchall()

        reply = ""

        if len(attackers) == 0:
            reply = "%s is not hit by anything as category %s" % (
                ship["name"],
                user_target,
            )
        else:
            if ship["class"].lower() == "roids":
                reply += "Capturing "
            elif ship["class"].lower() == "struct":
                reply += "Destroying "
            elif ship["class"].lower() == "rs":
                reply += "Looting "
            else:
                reply += "Stopping "
            reply += "%s %s (%s) as %s requires " % (
                self.format_real_value(ship_number),
                ship["name"],
                self.format_value(ship_number * ship["total_cost"]),
                user_target,
            )

            for a in attackers:
                if a["type"] == "Emp":
                    needed = int(
                        (
                            math.ceil(
                                ship_number
                                / (float(100 - ship["empres"]) / 100)
                                / a["gun"]
                            )
                        )
                        / efficiency
                    )
                else:
                    needed = int(
                        (math.ceil(float(total_armor) / a["damage"])) / efficiency
                    )
                reply += "%s: %s (%s) " % (
                    a["name"],
                    self.format_real_value(needed),
                    self.format_value(a["total_cost"] * needed),
                )

        irc_msg.reply(reply.strip())

        return 1
