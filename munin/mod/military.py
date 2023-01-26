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


class military(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 50)
        self.scan_prefix = "http://game.planetarion.com/showscan.pl?scan_id="
        self.paramsre = re.compile(r"(\d+)[. :-](\d+)[. :-](\d+)(?:\s+(base|[0-3]))?(?:\s+(l|li|lin|link|linkie))?")
        self.idre = re.compile(r"([a-z0-9]+)(?:\s+(base|[0-3]))?")
        self.usage = self.__class__.__name__ + "[<x:y:z> [fleet number or base] [link]] | [<scan ID> [fleet number or base]]"
        self.helptext = None

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        reply = ""

        m = self.paramsre.search(irc_msg.command_parameters)
        if m:
            # Get latest scan for planet at the given coordinates.
            x = m.group(1)
            y = m.group(2)
            z = m.group(3)
            print_fleet = self.parse_print_fleet(m, 4)
            link = not not m.group(5)

            p = loadable.planet(x=x, y=y, z=z)
            if p.load_most_recent(self.cursor, irc_msg.round):
                query = "SELECT s.tick,s.rand_id, h.name, m.fleet_index,m.amount"
                query += " FROM scan           AS s"
                query += " INNER JOIN military AS m ON s.id=m.scan_id"
                query += " INNER JOIN ship     AS h ON m.ship_id=h.id"
                query += " WHERE s.pid=%s AND s.id=(SELECT id FROM scan "
                query += "                          WHERE pid=s.pid"
                query += "                          AND scantype='military'"
                query += "                          AND ROUND=%s"
                query += "                          ORDER BY tick DESC"
                query += "                          LIMIT 1)"
                query += " AND h.round=%s"
                self.cursor.execute(query, (p.id, irc_msg.round, irc_msg.round,))

                if self.cursor.rowcount < 1:
                    reply += "No military scans available on %s:%s:%s" % (
                        p.x,
                        p.y,
                        p.z,
                    )
                else:
                    results = self.cursor.fetchall()
                    rand_id = results[0]["rand_id"]
                    reply += self.reply_military(link,
                                                 print_fleet,
                                                 rand_id,
                                                 p,
                                                 results,
                                                 results[0]["tick"],
                                                 irc_msg.round)
            else:
                reply += "No planet matching '%s:%s:%s' found" % (x, y, z)
        else:
            m = self.idre.search(irc_msg.command_parameters)
            if m:
                # Get specific scan by its ID.
                rand_id = m.group(1)
                print_fleet = self.parse_print_fleet(m, 2)
                link = False

                query = "SELECT p1.x,p1.y,p1.z, s.tick, h.name, m.fleet_index,m.amount"
                query += " FROM scan              AS s"
                query += " INNER JOIN military    AS m  ON s.id=m.scan_id"
                query += " INNER JOIN ship        AS h  ON h.id=m.ship_id"
                query += " INNER JOIN planet_dump AS p1 ON s.pid=p1.id AND s.round=p1.round"
                query += " INNER JOIN planet_dump AS p2 ON s.pid=p2.id AND s.tick=p2.tick AND s.round=p2.round"
                query += " WHERE p1.tick=(SELECT max_tick(%s::smallint)) AND s.rand_id=%s"
                self.cursor.execute(query, (irc_msg.round, rand_id,))

                if self.cursor.rowcount < 1:
                    reply += "No military scans matching ID %s" % (rand_id,)
                else:
                    results = self.cursor.fetchall()
                    x = results[0]["x"]
                    y = results[0]["y"]
                    z = results[0]["z"]
                    p = loadable.planet(x=x, y=y, z=z)
                    if p.load_most_recent(self.cursor, irc_msg.round):
                        reply += self.reply_military(link,
                                                     print_fleet,
                                                     rand_id,
                                                     p,
                                                     results,
                                                     results[0]["tick"],
                                                     irc_msg.round)
                    else:
                        # This shouldn't be possible, but just in case...
                        reply += "No planet matching '%s:%s:%s' found" % (x, y, z)
            else:
                irc_msg.reply("Usage: %s" % (self.usage,))
                return 0

        irc_msg.reply(reply)
        return 1

    def parse_print_fleet(self, match, group_index):
        if match.lastindex == group_index:
            print_fleet = match.group(group_index)
            return 0 if print_fleet == "base" else int(print_fleet)
        else:
            return -1

    def reply_military(self, link, print_fleet, rand_id, p, results, tick, cur_round):
        fleets = {
            0: [], # Base
            1: [], # Fleet 1
            2: [], # Fleet 2
            3: [], # Fleet 3
        }
        for result in results:
            fleet_index = int(result["fleet_index"])
            fleets[fleet_index] += [
                "%s %s" % (
                    result["name"],
                    result["amount"],
                )
            ]
        initial_reply = "Military scan on %s:%s:%s" % (
            p.x,
            p.y,
            p.z,
        )
        initial_reply += " (id: %s, age: %s, value diff: %s) " % (
            rand_id,
            self.current_tick(cur_round) - tick,
            p.vdiff(self.cursor, tick, cur_round),
        )
        reply = initial_reply
        fleet_strings = [
            "%s: %s" % (
                "Base" if fleet_index == 0 else "Fleet %d" % (fleet_index,),
                " | ".join(ships if len(ships) > 0 else ["<empty>"]),
            )
            for (fleet_index, ships) in fleets.items()
        ]
        if print_fleet < 0:
            reply += " // ".join(fleet_strings)
        else:
            reply += fleet_strings[print_fleet]

        too_long_string = ""
        if len(reply) > 450:
            too_long_string = " (Scan too long to show. Add fleet number or 'base' to show the ships in only one fleet)"
            link = True
        if link:
            reply = initial_reply
            reply += "%s%s%s" % (
                self.scan_prefix,
                rand_id,
                too_long_string,
            )
        return reply
