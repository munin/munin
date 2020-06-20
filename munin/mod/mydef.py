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


class mydef(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(\d)\s*x\s*(.*)", re.I)
        self.countre = re.compile(r"^(\d+(?:\.\d+)?[mk]?)$", re.I)
        self.shipre = re.compile(r"^(\w+),?$")
        self.nulls = ["<>", ".", "-", "?"]
        self.ship_classes = ["fi", "co", "fr", "de", "cr", "bs"]
        self.usage = (
            self.__class__.__name__ + " [fleets] x <[ship count] [ship name]> [comment]"
        )
        self.helptext = [
            "Add your fleets for defense listing. Ship can be a shipclass. For example !"
            + self.__class__.__name__
            + " 2x 20k Barghest 30k Harpy 20k BS Call me any time for hot shipsex."
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        u = self.load_user(user, irc_msg)
        if not u:
            return
        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        if not self.current_tick(irc_msg.round):
            irc_msg.reply("I don't know this round, what did you fuck up?")
            return 0

        fleetcount = m.group(1)
        garbage = m.group(2)
        reset_ships = False
        ships = {}
        comment = ""
        if garbage in self.nulls:
            reset_ships = True
        else:
            (ships, comment) = self.parse_garbage(garbage, irc_msg.round)

        (ships, comment) = self.reset_ships_and_comment(
            u, ships, fleetcount, irc_msg.round, comment, reset_ships
        )

        irc_msg.reply(
            "Updated your def info to: fleetcount %s, updated: pt%s ships: %s and comment: %s"
            % (
                fleetcount,
                self.current_tick(irc_msg.round),
                ", ".join(
                    [
                        "%s %s" % (self.format_real_value(x["ship_count"]), x["ship"])
                        for x in ships
                    ]
                ),
                comment,
            )
        )

        return 1

    def reset_ships_and_comment(
        self, user, ships, fleetcount, round, fleetcomment, reset_ships
    ):
        comment = self.update_comment_and_fleetcount(
            user, round, fleetcount, fleetcomment
        )
        if len(ships) > 0 or reset_ships:
            self.update_fleets(user, ships, round)
        ships = user.get_fleets(self.cursor, round)
        return (ships, comment)

    def update_fleets(self, user, ships, round):
        query = "DELETE FROM user_fleet WHERE user_id = %s AND round = %s"
        self.cursor.execute(query, (user.id, round,))

        for k in list(ships.keys()):
            query = "INSERT INTO user_fleet (user_id,round,ship,ship_count)"
            query += " VALUES (%s,%s,%s,%s)"
            args = (
                user.id,
                round,
                k,
                ships[k],
            )
            self.cursor.execute(query, args)

    def update_comment_and_fleetcount(self, user, round, fleetcount, fleetcomment):
        if fleetcomment != "":
            if fleetcomment in self.nulls:
                fleetcomment = ""

        tick = self.current_tick(round)

        query = "INSERT INTO round_user_pref (user_id,round,fleetcount,fleetcomment,fleetupdated) VALUES (%s,%s,%s,%s,%s)"
        query += " ON CONFLICT (user_id,round) DO"
        query += " UPDATE SET fleetcount=EXCLUDED.fleetcount, fleetcomment=EXCLUDED.fleetcomment, fleetupdated=EXCLUDED.fleetupdated"
        self.cursor.execute(query, (user.id, round, fleetcount, fleetcomment, tick))

        query = "SELECT fleetcomment FROM round_user_pref WHERE user_id=%s AND round=%s"
        self.cursor.execute(query, (user.id, round,))
        return self.cursor.fetchone()["fleetcomment"]

    def parse_garbage(self, garbage, round):
        parts = garbage.split()
        ships = {}
        while len(parts) > 1:
            mc = self.countre.match(parts[0])
            ms = self.shipre.match(parts[1])
            if not mc or not ms:
                break

            count = self.human_readable_number_to_integer(mc.group(1))
            ship = ms.group(1)

            s = self.get_ship_from_db(ship, round)

            if ship.lower() not in self.ship_classes and s:
                ship = s["name"]
            elif ship.lower() not in self.ship_classes:
                break

            ships[ship] = count

            parts.pop(0)
            parts.pop(0)
        comment = " ".join(parts)
        return (ships, comment)
