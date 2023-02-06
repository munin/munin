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


class fleets(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(.*)$")
        self.usage = self.__class__.__name__ + " <x:y:z>"
        self.ticks_back = 14
        self.max_fleets = 6

    def execute(self, user, access, irc_msg):
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.match(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        params = m.group(1)
        m = self.planet_coordre.search(params)

        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        x = m.group(1)
        y = m.group(2)
        z = m.group(3)

        planet = loadable.planet(x=x, y=y, z=z)
        if not planet.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply("No planet matching %s:%s:%s found" % (x, y, z))
            return 0

        self.cursor.execute("SELECT max_tick(%s::smallint)", (irc_msg.round,))
        current_tick = self.cursor.fetchone()["max_tick"]

        query = """
        SELECT target.x, target.y, target.z, fleet.fleet_size AS size, fleet.launch_tick, fleet.landing_tick AS land_tick, fleet.mission, fleet.fleet_name AS name
        FROM fleet
        INNER JOIN planet_dump AS owner  ON fleet.owner_id =  owner.id
        INNER JOIN planet_dump AS target ON fleet.target   = target.id
        WHERE fleet.round = %s
        AND owner.tick = %s
        AND target.tick = %s
        AND fleet.landing_tick > %s - %s
        AND (
            ( owner.x = %s AND  owner.y = %s AND  owner.z = %s AND fleet.mission != 'return')
            OR
            (target.x = %s AND target.y = %s AND target.z = %s AND fleet.mission  = 'return')
        )
        ORDER BY land_tick DESC
        """

        self.cursor.execute(query, (
            irc_msg.round,
            current_tick,
            current_tick,
            current_tick,
            self.ticks_back,
            x,
            y,
            z,
            x,
            y,
            z,
        ))

        rows = self.cursor.rowcount
        if rows:
            fleets = [
                self.fleet(
                    x=row["x"],
                    y=row["y"],
                    z=row["z"],
                    name=row["name"],
                    mission=row["mission"],
                    size=row["size"],
                    launch_tick=row["launch_tick"],
                    land_tick=row["land_tick"]
                )
                for row
                in self.cursor.fetchmany(self.max_fleets)
            ]
            irc_msg.reply("Location of the fleets of %s:%s:%s: %s%s" % (
                x,
                y,
                z,
                " | ".join([str(fleet) for fleet in fleets]),
                " (and %s more fleet)" % (rows - self.max_fleets,) if rows > self.max_fleets else "",
            ))
        else:
            irc_msg.reply("Cannot find any recent fleets of %s:%s:%s. Do you have a news scan and/or JGP?" % (
                x,
                y,
                z,
            ))
        return 1

    class fleet:
        def __init__(self,
                     *,
                     x,
                     y,
                     z,
                     name,
                     mission,
                     size,
                     launch_tick,
                     land_tick):
            self.x = x
            self.y = y
            self.z = z
            self.name = name
            self.mission = mission
            self.size = size
            self.launch_tick = launch_tick
            self.land_tick = land_tick

        def __str__(self):
            def tick_string(the_tick):
                return "unknown" if the_tick is None else "pt%s" % (the_tick,)
            return "Fleet \"%s\" is %sing%s %s:%s:%s (launch %s, land %s)" % (
                self.name,
                self.mission,
                " to" if self.mission == "return" else "",
                self.x,
                self.y,
                self.z,
                tick_string(self.launch_tick),
                tick_string(self.land_tick),
            )

