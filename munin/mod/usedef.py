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


class usedef(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(\S+)\s+(.*)")
        self.ship_classes = ["fi", "co", "fr", "de", "cr", "bs"]
        self.usage = self.__class__.__name__ + " <pnick> <ship>"
        self.helptext = None

    def execute(self, user, access, irc_msg):
        m = self.commandre.search(irc_msg.command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        taker = self.load_user(user, irc_msg)
        if not taker:
            return

        # assign param variables
        name = m.group(1)
        ships = m.group(2)
        u = self.load_user_from_pnick(name, irc_msg.round)
        if not u or u.userlevel < 100:
            irc_msg.reply("No members matching %s found" % (name,))
            return

        if u.fleetcount > 0:
            query = "UPDATE round_user_pref SET fleetcount = fleetcount - 1"
            query += " WHERE user_id=%s AND round=%s"
            self.cursor.execute(query, (u.id, irc_msg.round,))

        removed = self.drop_ships(u, taker, ships, irc_msg.round)
        reply = ""
        if u.fleetcount == 0:
            reply += (
                "%s's fleetcount was already 0, please ensure that they actually had a fleet free to launch."
                % (u.pnick,)
            )
        else:
            reply += "Removed a fleet for %s, they now have %s fleets left." % (
                u.pnick,
                u.fleetcount - 1,
            )
        reply += " Used the following ships: "
        reply += ", ".join(
            [
                "%s %s" % (self.format_real_value(removed[x]), x)
                for x in list(removed.keys())
            ]
        )
        irc_msg.reply(reply)
        return 1

    def drop_ships(self, user, taker, ships, round):
        ship_query = "SELECT ship, ship_count FROM user_fleet WHERE ship ilike %s AND round = %s AND user_id = %s"
        removed = {}
        for ship in ships.split():
            if ship not in self.ship_classes:
                ship_lookup = "%" + ship + "%"
            else:
                ship_lookup = ship
            self.cursor.execute(ship_query, (ship_lookup, round, user.id))
            for result in self.cursor.fetchall():
                s = result["ship"]
                c = result["ship_count"]
                removed[s] = c
                self.delete_ships(user, taker, s, c, round)
        return removed

    def delete_ships(self, user, taker, ship, count, round):
        delete_query = (
            "DELETE FROM user_fleet WHERE ship ilike %s AND round = %s AND user_id = %s"
        )
        self.cursor.execute(delete_query, (ship, round, user.id))
        log_query = "INSERT INTO fleet_log (taker_id,user_id,ship,ship_count,round)"
        log_query += " VALUES (%s,%s,%s,%s,%s)"
        self.cursor.execute(log_query, (taker.id, user.id, ship, count, round))
