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

        irc_msg.reply("Nope.")
        return 1

        x = m.group(1)
        y = m.group(2)
        z = m.group(3)

        planet = loadable.planet(x=x, y=y, z=z)
        if not planet.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply("No planet matching %s:%s:%s found" % (x, y, z))
            return 0

        self.cursor.execute("SELECT max_tick(%s::smallint)", (irc_msg.round,))
        current_tick = 350 # TODO: self.cursor.fetchone()["max_tick"]

        query = """
        SELECT target.x, target.y, target.z, fleet.fleet_size AS size, fleet.launch_tick, fleet.landing_tick AS land_tick, fleet.mission, fleet.fleet_name AS name
        FROM fleet
        INNER JOIN planet_dump AS owner  ON fleet.owner_id =  owner.id
        INNER JOIN planet_dump AS target ON fleet.target   = target.id
        WHERE fleet.round = %s
        AND owner.tick = (SELECT max_tick(%s::smallint))
        AND target.tick = (SELECT max_tick(%s::smallint))
        AND fleet.landing_tick > %s - 15
        AND owner.x = %s
        AND owner.y = %s
        AND owner.z = %s
        """

        self.cursor.execute(query, (
            irc_msg.round,
            irc_msg.round,
            irc_msg.round,
            current_tick,
            x,
            y,
            z,
        ))

        fleets = [
            self.fleet(
                row["x"],
                row["y"],
                row["z"],
                row["name"],
                row["mission"],
                row["size"],
                row["launch_tick"],
                row["land_tick"],
                current_tick
            )
            for row
            in self.cursor.fetchall()
        ]
        # We do this twice. The first time, outgoing fleets may be
        # converted to returning fleets, which need to be recalculated
        # a second time.
        for i in [1,2]:
            for f in fleets:
                f.recalculate(current_tick)

        if len(fleets) > 0:
            irc_msg.reply("Location of the fleets of %s:%s:%s: %s" % (
                x,
                y,
                z,
                ' | '.join([str(fleet) for fleet in fleets]),
            ))
        else:
            irc_msg.reply("Cannot find any recent fleets of %s:%s:%s. Do you have a news scan?" % (
                x,
                y,
                z,
            ))
            return 1

    class fleet:
        def __init__(self,
                     x,
                     y,
                     z,
                     name,
                     mission,
                     size,
                     launch,
                     land,
                     current):
            self.x = x
            self.y = y
            self.z = z
            self.name = name
            self.mission = mission
            self.size = size
            self.launch = launch
            self.land = land
            self.current = current
            self.earliest_return = None
            self.latest_return = None

        def tick_string(self, the_tick):
            return "unknown" if the_tick is None else "pt%s" % (the_tick,)

        def recalculate(self, the_tick):
            # Algorithm
            #
            # For each fleet, inspect the mission:
            # - Fleet is returning. Inspect land tick.
            #   + If land tick <= current tick: fleet has returned home, don't display.
            #   + Otherwise: fleet is certainly still returning, display.
            # - Fleet is outgoing. Inspect land tick.
            #   + If land tick <= current tick: fleet has landed for sure, convert to returning fleet with adjusted eta and rerun the algorithm.
            #   + Otherwise: fleet has either been recalled or is still going

            # TODO: Use scan tick, not current tick!
            pass

        def __str__(self):
            mission_string = "%sing%s" % (
                self.mission,
                " from" if self.mission == "return" else "",
            )
            earliest_return_string = ", return unknown"
            latest_return_string = ""
            if self.earliest_return:
                earliest_return_string = ", earliest return pt%s" % (
                    self.earliest_return
                )
            if self.latest_return:
                latest_latest_return = ", latest return pt%s" %(
                    self.latest_return,
                )
            return "Fleet \"%s\" is %s %s:%s:%s (launch %s, land %s%s%s)" % (
                self.name,
                mission_string,
                self.x,
                self.y,
                self.z,
                self.tick_string(self.launch),
                self.tick_string(self.land),
                earliest_return_string,
                latest_return_string,
            )

