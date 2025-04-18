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

# This module has nothing alliance specific as far as I can tell.
# qebab, 24/6/08.

import re
from munin import loadable


class roidcost(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(\d+)\s+(\d+[TtBbMmKk]?)(\s+(\d+))?", re.I)
        self.usage = self.__class__.__name__ + " <roids> <_value_ cost> [mining_bonus]"

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        roids = int(m.group(1))
        cost = self.human_readable_number_to_integer(m.group(2))
        bonus = m.group(4) or 0
        bonus = int(bonus)

        mining = 250

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        if roids == 0:
            irc_msg.reply("Another NewDawn landing, eh?")
            return 1

        mining = mining * ((float(bonus) + 100) / 100)

        repay = int((cost * 100) / (roids * mining))
        reply = (
            "Capping %s roids at %s value with %s%% bonus will repay in %s ticks (%s days)"
            % (roids, self.format_value(cost * 100), bonus, repay, round(repay / 24))
        )

        repay_demo = int(
            (cost * 100)
            / (
                roids
                * mining
                * (
                    1
                    / (
                        1
                        - float(
                            self.config.get("Planetarion", "democracy_cost_reduction")
                        )
                    )
                )
            )
        )
        reply += " Democracy: %s ticks (%s days)" % (repay_demo, round(repay_demo / 24))

        repay_tota = int(
            (cost * 100)
            / (
                roids
                * mining
                * (
                    1
                    / (
                        1
                        - float(
                            self.config.get(
                                "Planetarion", "totalitarianism_cost_reduction"
                            )
                        )
                    )
                )
            )
        )
        reply += " Totalitarianism: %s ticks (%s days)" % (
            repay_tota,
            round(repay_tota / 24),
        )

        irc_msg.reply(reply)

        return 1
