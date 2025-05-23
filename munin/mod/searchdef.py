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


class searchdef(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(\d+(?:\.\d+)?[TtBbMmKk]?)\s+(\S+)")
        self.ship_classes = ["fi", "co", "fr", "de", "cr", "bs"]
        self.usage = self.__class__.__name__ + " <number> <ship>"
        self.helptext = None

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        count = self.human_readable_number_to_integer(m.group(1))
        ship = m.group(2)

        if ship not in self.ship_classes:
            ship_lookup = "%" + ship + "%"
        else:
            ship_lookup = ship

        query = "SELECT u.pnick, p.fleetcount, p.fleetcomment, p.fleetupdated, f.ship, f.ship_count"
        query += " FROM       user_fleet      AS f"
        query += " INNER JOIN user_list       AS u ON u.id=f.user_id"
        query += " LEFT JOIN  round_user_pref AS p ON u.id=p.user_id"
        query += " WHERE f.round = %s"
        query += " AND p.round = %s"
        query += " AND f.ship ILIKE %s"
        query += " AND f.ship_count >= %s"
        query += " AND p.fleetcount > 0"
        query += " ORDER BY f.ship_count DESC"
        self.cursor.execute(query, (irc_msg.round, irc_msg.round, ship_lookup, count,))

        if self.cursor.rowcount < 1:
            irc_msg.reply(
                "There are no planets with free fleets and at least %s ships matching '%s'"
                % (self.format_real_value(count), ship)
            )
            return

        reply = "Fleets matching query: "
        reply += ", ".join(
            [
                "%s(%s) %s: %s %s"
                % (
                    x["pnick"],
                    x["fleetupdated"] - self.current_tick(irc_msg.round),
                    x["fleetcount"],
                    self.format_real_value(x["ship_count"]),
                    x["ship"],
                )
                for x in self.cursor.fetchall()
            ]
        )

        irc_msg.reply(reply)

        return 1
