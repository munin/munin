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
        self.paramre = re.compile(r"^\s*(\S+)\s+(fi|co|fr|de|cr|bs)", re.IGNORECASE)
        self.ship_classes = ["fi", "co", "fr", "de", "cr", "bs"]
        self.usage = self.__class__.__name__ + " <alliance> <target ship class>"
        self.helptext = None
        self.mapping = {
            "fi": "Fighter",
            "co": "Corvette",
            "fr": "Frigate",
            "de": "Destroyer",
            "cr": "Cruiser",
            "bs": "Battleship",
        }

    def execute(self, user, access, irc_msg):
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        param_m = self.paramre.search(irc_msg.command_parameters)
        if not param_m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        alliance_name = param_m.group(1)
        target_class = self.mapping[param_m.group(2).lower()]
        # lookup alliance
        a = loadable.alliance(name=alliance_name)
        if not a.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply(f"No alliance matching {alliance_name} found")
            return

        # get all members from intel left join scans?
        intels = self.get_all_members(irc_msg, a)

        fresh_scans = self.get_fresh_au_scans(irc_msg, a)
        ships = self.get_ships_from_fresh_scans(irc_msg, a, target_class)
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
        print(t1)
        irc_msg.reply(
            f"{a.name} ({a.members} members, {len(intels)} in intel, {len(fresh_scans)} with fresh scans) has {total_value} oommph against {target_class}: {' '.join(t1)} | {' '.join(t2)} | {' '.join(t3)}"
        )
        return 1

    def get_all_members(self, irc_msg, alliance):
        query = "SELECT * FROM intel WHERE round = %s and alliance_id = %s"
        self.cursor.execute(
            query,
            (
                irc_msg.round,
                alliance.id,
            ),
        )
        return self.cursor.fetchall()

    def get_fresh_au_scans(self, irc_msg, alliance):
        query = "SELECT * FROM ("
        query += " SELECT *,rank() OVER (PARTITION BY t1.pid ORDER BY t1.id DESC) AS rank FROM scan AS t1"
        query += " WHERE t1.round = %s"
        query += " AND t1.tick > (select max_tick(%s::smallint) - 48)"
        query += " AND scantype = 'au'"
        query += " AND pid in ("
        query += "  SELECT pid FROM intel AS t4"
        query += "  WHERE t4.round = %s and t4.alliance_id = %s"
        query += ") ) AS scans"
        query += " WHERE rank = 1"
        self.cursor.execute(
            query, (irc_msg.round, irc_msg.round, irc_msg.round, alliance.id)
        )
        return self.cursor.fetchall()

    def get_ships_from_fresh_scans(self, irc_msg, alliance, target_class):
        query = "SELECT name,target_1,target_2,target_3,sum(total_cost) AS total_cost, sum(amount) AS amount FROM ("
        query += " SELECT t1.id AS scan_id,t1.tick,t1.pid,t2.amount,t3.*,rank() OVER (PARTITION BY t1.pid ORDER BY t1.id DESC) AS rank FROM scan AS t1"
        query += " INNER JOIN au AS t2 on t2.scan_id = t1.id"
        query += " INNER JOIN ship AS t3 on t3.id = t2.ship_id "
        query += " WHERE t1.round = %s"
        query += " AND t1.tick > (select max_tick(%s::smallint) - 48)"
        query += " AND pid in ("
        query += "  SELECT pid FROM intel AS t4"
        query += "  WHERE t4.round = %s and t4.alliance_id = %s"
        query += ")"
        query += " AND (t3.target_1 = %s OR t3.target_2 = %s OR t3.target_3 = %s)"
        query += ") ships"
        query += " WHERE rank = 1"
        query += " GROUP BY name, target_1, target_2, target_3"
        self.cursor.execute(
            query,
            (
                irc_msg.round,
                irc_msg.round,
                irc_msg.round,
                alliance.id,
                target_class,
                target_class,
                target_class,
            ),
        )
        return self.cursor.fetchall()
