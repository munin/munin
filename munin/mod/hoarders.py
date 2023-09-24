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

import re
import munin.loadable as loadable


class hoarders(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(?:0*([0-9]+)[: .]0*([0-9]+)(?:[: .]0*([0-9]+))?)|(\S+)", re.IGNORECASE)
        self.usage = self.__class__.__name__ + " <x:y[:z]|alliance name>"
        self.helptext = [
            "Return the stockpile and the amount of resources in production of"
            " a planet, galaxy, or alliance."
        ]
        self.maximum_scan_age = 12

    def execute(self, user, access, irc_msg):
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        param_m = self.paramre.search(irc_msg.command_parameters)
        if not param_m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        x = param_m.group(1)
        y = param_m.group(2)
        z = param_m.group(3)
        alliance_name = param_m.group(4)

        if x and y:
            if z:
                planet = loadable.planet(x=x, y=y, z=z)
                if not planet.load_most_recent(self.cursor, irc_msg.round):
                    irc_msg.reply("No planet matching %s:%s:%s found" % (x, y, z,))
                    return
                irc_msg.reply(self.planet_hoarders(
                    irc_msg.round,
                    planet,
                ))
            else:
                galaxy = loadable.galaxy(x=x, y=y)
                if not galaxy.load_most_recent(self.cursor, irc_msg.round):
                    irc_msg.reply("No galaxy matching %s:%s found" % (x, y,))
                    return
                irc_msg.reply(self.galaxy_hoarders(
                    irc_msg.round,
                    galaxy,
                ))
        else:
            alliance = loadable.alliance(name=alliance_name)
            if not alliance.load_most_recent(self.cursor, irc_msg.round):
                irc_msg.reply("No alliance matching %s found" % (alliance_name,))
                return
            irc_msg.reply(self.alliance_hoarders(
                irc_msg.round,
                alliance,
            ))
        return 1

    def alliance_hoarders(self, round, alliance):
        counting_members = int(self.config.get("Planetarion", "counting_tag_members"))
        query = """
        SELECT score, res, prod
        FROM (
            SELECT p.score, (ps.res_metal + ps.res_crystal + ps.res_eonium) AS res, ps.prod_res AS prod, rank() OVER (PARTITION BY s.pid ORDER BY s.id DESC) AS rank
            FROM            planet_dump   AS p
            INNER      JOIN intel         AS i  ON i.pid         = p.id
            INNER      JOIN alliance_dump AS a  ON i.alliance_id = a.id AND p.tick = a.tick
            LEFT OUTER JOIN scan          AS s  ON s.pid         = p.id
            LEFT OUTER JOIN planet        AS ps ON s.id          = ps.scan_id
            WHERE p.tick = max_tick(%s::smallint)
            AND a.id = %s
            AND (
                s.tick >= max_tick(%s::smallint) - %s
                OR
                s.tick IS NULL
            )
        ) AS scans
        WHERE rank = 1
        ORDER BY score DESC
        LIMIT %s
        """
        args = (
            round,
            alliance.id,
            round,
            self.maximum_scan_age,
            counting_members,
        )
        self.cursor.execute(query, args)
        stockpile = 0
        in_production = 0
        scan_count = 0
        for row in self.cursor.fetchall():
            if row['res'] is not None:
                scan_count += 1
                stockpile += row['res']
                in_production += row['prod']

        min_potential_score = alliance.score + stockpile / 100 - stockpile / 150
        max_potential_score = alliance.score + (stockpile + in_production) /  94 - (stockpile + in_production) / 150
        return "%s (%s members, %s counting, %s with fresh scans) has %s score, %s resources stockpiled, %s resources in production | Potential score: %s-%s" % (
            alliance.name,
            alliance.members,
            counting_members if alliance.members > counting_members else "all",
            scan_count if counting_members > scan_count else "all",
            self.format_real_value(alliance.score),
            self.format_real_value(stockpile),
            self.format_real_value(in_production),
            self.format_real_value(min_potential_score),
            self.format_real_value(max_potential_score),
        )

    def galaxy_hoarders(self, round, galaxy):
        return "hoarders galaxy %s:%s WIP" % (galaxy.x, galaxy.y,)

    def planet_hoarders(self, round, planet):
        return "hoarders planet %s:%s:%s WIP" % (planet.x, planet.y, planet.z,)
