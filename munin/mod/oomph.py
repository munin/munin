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


class oomph(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(((0*[0-9]+)[: .](0*[0-9]+))|(\S+))\s+(fi|co|fr|de|cr|bs)", re.IGNORECASE)
        self.ship_classes = ["fi", "co", "fr", "de", "cr", "bs"]
        self.usage = self.__class__.__name__ + " <x:y|alliance name> <target ship class>"
        self.helptext = None
        self.mapping = {
            "fi": "Fighter",
            "co": "Corvette",
            "fr": "Frigate",
            "de": "Destroyer",
            "cr": "Cruiser",
            "bs": "Battleship",
        }
        self.maximum_scan_age = 48

    def execute(self, user, access, irc_msg):
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        param_m = self.paramre.search(irc_msg.command_parameters)
        if not param_m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        target_class = self.mapping[param_m.group(6).lower()]

        galaxy_x = param_m.group(3)
        galaxy_y = param_m.group(4)
        if galaxy_x and galaxy_y:
            irc_msg.reply(self.galaxy_oomph(
                irc_msg.round,
                galaxy_x,
                galaxy_y,
                target_class
            ))

        else:
            alliance_name = param_m.group(5)
            # lookup alliance
            alliance = loadable.alliance(name=alliance_name)
            if not alliance.load_most_recent(self.cursor, irc_msg.round):
                irc_msg.reply(f"No alliance matching {alliance_name} found")
                return
            irc_msg.reply(self.alliance_oomph(
                irc_msg.round,
                alliance,
                target_class
            ))
        return 1

    def alliance_oomph(self, round, alliance, target_class):

        # get all members from intel left join scans?
        alliance_members = self.get_alliance_member_count(round, alliance)

        fresh_scan_count = self.get_fresh_au_scan_count_alliance(round, alliance)
        ships = self.get_ships_from_fresh_scans_alliance(round, alliance, target_class)

        total_value = self.format_value(
            sum([s["total_cost"] * s["amount"] for s in ships])
        )

        t1 = [
            f"{self.format_real_value(s['amount'])} {s['name']}"
            for s in ships
            if s["target_1"] == target_class
        ]
        t2 = [
            f"{self.format_real_value(s['amount'])} {s['name']} (t2)"
            for s in ships
            if s["target_2"] == target_class
        ]
        t3 = [
            f"{self.format_real_value(s['amount'])} {s['name']} (t3)"
            for s in ships
            if s["target_3"] == target_class
        ]
        return f"{alliance.name} ({alliance.members} members, {alliance_members} in intel, {fresh_scan_count} with fresh scans) has {total_value} oommph against {target_class}: {' '.join(t1)} | {' '.join(t2) or 'None (t2)'} | {' '.join(t3) or 'None (t3)'}"

    def get_alliance_member_count(self, round, alliance):
        query = "SELECT count(*) AS count FROM intel WHERE round = %s and alliance_id = %s"
        self.cursor.execute(
            query,
            (
                round,
                alliance.id,
            ),
        )
        return self.cursor.fetchone()['count']

    def get_fresh_au_scan_count_alliance(self, round, alliance):
        query = "SELECT count(*) AS count FROM ("
        query += " SELECT DISTINCT ON (s.rand_id) rank() OVER (PARTITION BY s.pid ORDER BY s.id DESC) AS rank"
        query += " FROM scan AS s"
        query += " INNER JOIN au AS a on a.scan_id = s.id"
        query += " WHERE s.round = %s"
        query += " AND s.tick > (select max_tick(%s::smallint) - %s)"
        query += " AND pid in ("
        query += "  SELECT pid FROM intel AS i"
        query += "  WHERE i.round = %s and i.alliance_id = %s"
        query += ") ) AS scans"
        query += " WHERE rank = 1"
        self.cursor.execute(
            query, (
                round,
                round,
                self.maximum_scan_age,
                round,
                alliance.id,
            ),
        )
        return self.cursor.fetchone()['count']

    def get_ships_from_fresh_scans_alliance(self, round, alliance, target_class):
        query = "SELECT name,target_1,target_2,target_3,sum(total_cost) AS total_cost, sum(amount) AS amount FROM ("
        query += " SELECT s.id AS scan_id,s.tick,s.pid,a.amount,sh.*,rank() OVER (PARTITION BY s.pid ORDER BY s.id DESC) AS rank"
        query += " FROM scan AS s"
        query += " INNER JOIN au AS a on a.scan_id = s.id"
        query += " INNER JOIN ship AS sh on sh.id = a.ship_id "
        query += " WHERE s.round = %s"
        query += " AND s.tick > (select max_tick(%s::smallint) - %s)"
        query += " AND pid in ("
        query += "  SELECT pid FROM intel AS i"
        query += "  WHERE i.round = %s and i.alliance_id = %s"
        query += ")"
        query += " AND (sh.target_1 = %s OR sh.target_2 = %s OR sh.target_3 = %s)"
        query += ") ships"
        query += " WHERE rank = 1"
        query += " GROUP BY name, target_1, target_2, target_3"
        self.cursor.execute(
            query,
            (
                round,
                round,
                self.maximum_scan_age,
                round,
                alliance.id,
                target_class,
                target_class,
                target_class,
            ),
        )
        return self.cursor.fetchall()

    def galaxy_oomph(self, round, x, y, target_class):
        galaxy_members = self.get_galaxy_member_count(round,
                                                      x,
                                                      y)
        if galaxy_members == 0:
            return f"No galaxy {x}:{y} found"

        fresh_scan_count = self.get_fresh_au_scan_count_galaxy(round,
                                                               x,
                                                               y)
        ships = self.get_ships_from_fresh_scans_galaxy(round,
                                                       x,
                                                       y,
                                                       target_class)
        total_value = self.format_value(
            sum([s["total_cost"] * s["amount"] for s in ships])
        )

        t1 = [
            f"{self.format_real_value(s['amount'])} {s['name']}"
            for s in ships
            if s["target_1"] == target_class
        ]
        t2 = [
            f"{self.format_real_value(s['amount'])} {s['name']} (t2)"
            for s in ships
            if s["target_2"] == target_class
        ]
        t3 = [
            f"{self.format_real_value(s['amount'])} {s['name']} (t3)"
            for s in ships
            if s["target_3"] == target_class
        ]
        return f"{x}:{y} ({galaxy_members} members, {fresh_scan_count} with fresh scans) has {total_value} oommph against {target_class}: {' '.join(t1)} | {' '.join(t2) or 'None (t2)'} | {' '.join(t3) or 'None (t3)'}"

    def get_galaxy_member_count(self, round, x, y):
        query = """
            SELECT count(*) AS count
            FROM planet_dump
            WHERE round = %s
            AND tick = (select max_tick(%s::smallint))
            AND x = %s
            AND y = %s;
        """
        self.cursor.execute(
            query,
            (
                round,
                round,
                x,
                y,
            ),
        )
        return self.cursor.fetchone()['count']

    def get_fresh_au_scan_count_galaxy(self, round, x, y):
        query = """
            SELECT count(*) AS count FROM (
            SELECT DISTINCT ON (s.rand_id) rank() OVER (PARTITION BY s.pid ORDER BY s.id DESC) AS rank
            FROM scan AS s
                INNER JOIN planet_dump AS p ON p.id = s.pid AND s.tick = p.tick
                INNER JOIN au AS a on a.scan_id = s.id
                WHERE s.round = %s
                AND s.tick > (select max_tick(%s::smallint) - %s)
                AND p.x = %s
                AND p.y = %s
            ) AS ships
            WHERE rank = 1;
        """
        self.cursor.execute(
            query, (
                round,
                round,
                x,
                y,
            ),
        )
        return self.cursor.fetchone()['count']

    def get_ships_from_fresh_scans_galaxy(self, round, x, y, target_class):
        query = """
            SELECT name, target_1, target_2, target_3, sum(total_cost) AS total_cost, sum(amount) AS amount FROM (
                SELECT s.id AS scan_id, s.tick, s.pid, a.amount, sh.*, rank() OVER (PARTITION BY s.pid ORDER BY s.id DESC) AS rank FROM scan AS s
                    INNER JOIN planet_dump AS p ON p.id = s.pid AND s.tick = p.tick
                    INNER JOIN au AS a ON a.scan_id = s.id
                    INNER JOIN ship AS sh ON a.ship_id = sh.id
                    WHERE s.round = %s
                    AND s.tick > (select max_tick(%s::smallint) - %s)
                    AND p.x = %s
                    AND p.y = %s
                    AND (sh.target_1 = %s OR sh.target_2 = %s OR sh.target_3 = %s)
                ) AS ships
            WHERE rank = 1
            GROUP BY name, target_1, target_2, target_3;
        """
        self.cursor.execute(
            query,
            (
                round,
                round,
                self.maximum_scan_age,
                x,
                y,
                target_class,
                target_class,
                target_class,
            ),
        )
        return self.cursor.fetchall()
