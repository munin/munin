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

import re
from munin import loadable


class bonus(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^(\s*([0-9]+))?$")
        self.usage = self.__class__.__name__ + " [tick]"
        self.helptext = [
            "Show bonus amounts at the specified tick (or the current one if none is given)"
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        tick = m.group(2)
        if tick is None:
            self.cursor.execute("SELECT max_tick(%s::smallint)", (irc_msg.round,))
            tick = self.cursor.fetchone()['max_tick']
        tick = int(tick)

        resource_bonus = 10000 + 4800 * tick
        asteroid_bonus = 6 + int(0.15 * tick)
        research_bonus = 4000 + 24 * tick
        construction_bonus = 2000 + 18 * tick

        reply = "Resource bonus at tick %d: %s of EACH, asteroid bonus: %s of EACH, research bonus: %s, construction bonus: %s" % (
            tick, resource_bonus, asteroid_bonus, research_bonus, construction_bonus,)

        u = loadable.user(pnick=irc_msg.user)
        if u.load_from_db(self.cursor, irc_msg.round):
            # Since we don't store the number of roids of each type, assume the
            # roid numbers are about equal.
            existing_asteroids = round(u.planet.size / 3)
            new_total_asteroids = existing_asteroids + asteroid_bonus
            init_cost = int(
                5/6 * (new_total_asteroids * (new_total_asteroids + 1) * (new_total_asteroids + 2) -
                       existing_asteroids * (existing_asteroids + 1) * (existing_asteroids + 2))
            )
            reply += " | cur roids %s, initcost %s" % (existing_asteroids, init_cost,)
            if init_cost < resource_bonus:
                reply += " | You can initiate more roids with the resource bonus than the asteroid bonus gives!"

        irc_msg.reply(reply)
        return 1
