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
            "Find out the amount of resources a planet, galaxy, or alliance has"
            " stockpiled and in production, and then calculate what their"
            " potential minimum and maximum total score is when it is all"
            " converted into value."
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
        counting_members = int(self.config.get("Planetarion",
                                               "counting_tag_members"))
        query = """
        SELECT *
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
        rows = self.cursor.fetchall()
        scan_count = len([1 for row in rows if row['res'] is not None])
        prefix = "%s (%s members, %s counting, %s with fresh scans)" % (
            alliance.name,
            alliance.members,
            counting_members if alliance.members > counting_members else "all",
            scan_count if counting_members > scan_count else "all",
        )
        return self.process_and_format_hoarders(prefix,
                                                alliance.score,
                                                rows)

    def galaxy_hoarders(self, round, galaxy):
        query = """
        SELECT *
        FROM (
            SELECT (ps.res_metal + ps.res_crystal + ps.res_eonium) AS res, ps.prod_res AS prod, rank() OVER (PARTITION BY s.pid ORDER BY s.id DESC) AS rank
            FROM            planet_dump   AS p
            LEFT OUTER JOIN scan          AS s  ON s.pid         = p.id
            LEFT OUTER JOIN planet        AS ps ON s.id          = ps.scan_id
            WHERE p.round = %s
            AND p.tick = max_tick(%s::smallint)
            AND p.x = %s
            AND p.y = %s
            AND (
                s.tick >= max_tick(%s::smallint) - %s
                OR
                s.tick IS NULL
            )
        ) AS scans
        WHERE rank = 1
        """
        # Constrain on (round, tick, x, y) to take advantage of the
        # planet_dump_pkey index on planet_dump.
        args = (
            round,
            round,
            galaxy.x,
            galaxy.y,
            round,
            self.maximum_scan_age,
        )
        self.cursor.execute(query, args)
        rows = self.cursor.fetchall()
        scan_count = len([1 for row in rows if row['res'] is not None])
        prefix = "%s:%s (%s members, %s with fresh scans)" % (
            galaxy.x,
            galaxy.y,
            galaxy.members,
            scan_count if galaxy.members > scan_count else "all",
        )
        return self.process_and_format_hoarders(prefix,
                                                galaxy.score,
                                                rows)

    def planet_hoarders(self, round, planet):
        query = """
        SELECT *
        FROM (
            SELECT (ps.res_metal + ps.res_crystal + ps.res_eonium) AS res, ps.prod_res AS prod, rank() OVER (PARTITION BY s.pid ORDER BY s.id DESC) AS rank
            FROM            planet_dump   AS p
            LEFT OUTER JOIN scan          AS s  ON s.pid         = p.id
            LEFT OUTER JOIN planet        AS ps ON s.id          = ps.scan_id
            WHERE p.round = %s
            AND p.tick = max_tick(%s::smallint)
            AND p.x = %s
            AND p.y = %s
            AND p.z = %s
            AND (
                s.tick >= max_tick(%s::smallint) - %s
                OR
                s.tick IS NULL
            )
        ) AS scans
        WHERE rank = 1
        """
        # Constrain on (round, tick, x, y, z) to take advantage of the
        # planet_dump_pkey index on planet_dump.
        args = (
            round,
            round,
            planet.x,
            planet.y,
            planet.z,
            round,
            self.maximum_scan_age,
        )
        self.cursor.execute(query, args)
        rows = self.cursor.fetchall()
        if rows[0]['res'] is None:
            return "Need a fresh planet scan on %s:%s:%s!" % (
            planet.x,
            planet.y,
            planet.z,
        )
        else:
            prefix = "%s:%s:%s" % (
                planet.x,
                planet.y,
                planet.z,
            )
            return self.process_and_format_hoarders(prefix,
                                                    planet.score,
                                                    rows)

    def process_and_format_hoarders(self, prefix, score, rows):
        stockpile     = sum([row['res']  for row in rows if row['res']  is not None])
        in_production = sum([row['prod'] for row in rows if row['prod'] is not None])
        minimum_potential_score = self.minimum_potential_score(score,
                                                               stockpile)
        maximum_potential_score = self.maximum_potential_score(score,
                                                               stockpile,
                                                               in_production)
        return "%s has %s score, %s resources stockpiled, %s resources in production | Potential total score: %s-%s" % (
            prefix,
            self.format_real_value(score),
            self.format_real_value(stockpile),
            self.format_real_value(in_production),
            self.format_real_value(minimum_potential_score),
            self.format_real_value(maximum_potential_score),
        )

    def minimum_potential_score(self, score, stockpile):
        # If all production orders are /almost/ finished, then their owner has
        # already gained all the value they can from them, so we can safely
        # ignore it here.
        return score + stockpile / 100 - stockpile / 150

    def maximum_potential_score(self, score, stockpile, in_production):
        # Production orders give 0 extra value if the game hasn't ticked since
        # they were started, in which case we should treat it as if it were a
        # stockpile. We also assume Totalitarianism here, because it adds a
        # little more value.
        return score + (stockpile + in_production) / 94 - (stockpile + in_production) / 150
