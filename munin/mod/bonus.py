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
import math
from munin import loadable


class bonus(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^(?:\s*([0-9.]+))(?:\s*([0-9]+))?\s*$")
        self.usage = self.__class__.__name__ + " [mining bonus] [tick]"
        self.helptext = [
            "Show bonus amounts at the specified tick (or the current one if "
            "none is given). You can also pass in your mining bonus."
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        self.cursor.execute("SELECT max_tick(%s::smallint)", (irc_msg.round,))
        tick = int(self.cursor.fetchone()['max_tick'])
        bonus = 25

        m = self.paramre.search(irc_msg.command_parameters)
        if m:
            try:
                float_num = float(m.group(1))
                int_num = int(float_num)
                if float_num > 200 and m.lastindex < 2 and int_num == float_num:
                    # Only one argument given and it's an integer too big to be
                    # a reasonable mining bonus. User probably meant to pass in
                    # a tick instead.
                    tick = int_num
                else:
                    bonus = float_num
            except:
                pass
            if m.lastindex >= 2:
                tick = int(m.group(2))

        resource_bonus = 10000 + 4800 * tick
        asteroid_bonus = 6 + int(0.15 * tick)
        research_bonus = 4000 + 24 * tick
        construction_bonus = 2000 + 18 * tick

        reply = "Resource bonus at tick %d: %s of EACH, asteroid bonus: %s of EACH, research bonus: %s, construction bonus: %s" % (
            tick, resource_bonus, asteroid_bonus, research_bonus, construction_bonus,)

        u = loadable.user(pnick=irc_msg.user)
        more = False
        if u.load_from_db(self.cursor, irc_msg.round) and u.planet:
            # Since we don't store the number of roids of each type, assume the
            # roid numbers are about equal.
            existing_asteroids = round(u.planet.size / 3)
            new_total_asteroids = existing_asteroids + asteroid_bonus
            init_cost = int(
                5/6 * (new_total_asteroids * (new_total_asteroids + 1) * (new_total_asteroids + 2) -
                       existing_asteroids * (existing_asteroids + 1) * (existing_asteroids + 2))
            )
            if init_cost < resource_bonus:
                reply += " | You can initiate more roids with the resource bonus than the asteroid bonus gives!"
                more = True
        if not more:
            ticks = math.ceil(resource_bonus / (asteroid_bonus * 250 * (1 + bonus/100.0)))
            reply += " | You will mine more from the asteroids in %d ticks with %s%% mining bonus" % (
                ticks,
                bonus,
            )

        irc_msg.reply(reply)
        return 1
