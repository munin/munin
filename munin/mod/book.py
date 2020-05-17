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

# Removed ascendancy specific things. I think.
# qebab, 22/06/08

import re
import psycopg2
from munin import loadable


class book(loadable.loadable):
    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 50)
        self.paramre = re.compile(r"^\s+(\d+)[. :-](\d+)[. :-](\d+)\s+(\d+)(\s+(yes))?")
        self.usage = self.__class__.__name__ + " <x:y:z> (<eta>|<landing tick>)"
        self.helptext = [
            "Book a target for attack. You should always book your targets, someone doesn't inadvertedly piggy your attack."
        ]

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0

        m = self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        when = int(m.group(4))
        override = m.group(6)

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        if access < 100 and not irc_msg.user:
            irc_msg.reply(
                "I don't trust you. You have to set mode +x to book a target."
            )
            return 0

        p = loadable.planet(x=x, y=y, z=z)
        if not p.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply("No planet matching '%s:%s:%s' found" % (x, y, z))
            return 1
        else:
            i = loadable.intel(pid=p.id)
            if not i.load_from_db(self.cursor, irc_msg.round):
                pass
            else:
                if (
                    i
                    and i.alliance
                    and i.alliance.lower()
                    == self.config.get("Auth", "alliance").lower()
                ):
                    irc_msg.reply(
                        "%s:%s:%s is %s in %s. Quick, launch before they notice the highlight."
                        % (
                            x,
                            y,
                            z,
                            i.nick or "someone",
                            self.config.get("Auth", "alliance"),
                        )
                    )
                    return 0
        curtick = self.current_tick(irc_msg.round)
        tick = -1
        eta = -1

        if when < 32:
            tick = curtick + when
            eta = when
        elif when < curtick:
            irc_msg.reply(
                "Can not book targets in the past. You wanted tick %s, but current tick is %s."
                % (when, curtick)
            )
            return 1
        else:
            tick = when
            eta = tick - curtick
        if tick > 32767:
            tick = 32767

        query = "SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid, t2.pnick AS pnick, t2.userlevel AS userlevel, t3.x AS x, t3.y AS y, t3.z AS z"
        query += " FROM target AS t1"
        query += " INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
        query += " LEFT JOIN user_list AS t2 ON t1.uid=t2.id"
        query += " WHERE t1.tick > %s"
        query += " AND t3.tick = (SELECT max_tick(%s::smallint)) AND t3.round=%s"
        query += " AND t3.x=%s AND t3.y=%s AND t3.z=%s"

        self.cursor.execute(query, (tick, irc_msg.round, irc_msg.round, x, y, z,))

        if self.cursor.rowcount > 0 and not override:
            reply = (
                "There are already bookings for that target after landing pt %s (eta %s). To see status on this target, do !status %s:%s:%s."
                % (tick, eta, x, y, z)
            )
            reply += (
                " To force booking at your desired eta/landing tick, use !book %s:%s:%s %s yes (Bookers:"
                % (x, y, z, tick)
            )
            prev = []
            for r in self.cursor.fetchall():
                owner = "nick:" + r["nick"]
                if r["pnick"]:
                    owner = "user:" + r["pnick"]
                    prev.append("(%s %s)" % (r["tick"], owner))
            reply += " " + ", ".join(prev)
            reply += " )"
            irc_msg.reply(reply)
            return 1

        uid = None
        if irc_msg.user:
            u = loadable.user(pnick=irc_msg.user)
            if u.load_from_db(self.cursor, irc_msg.round):
                uid = u.id

        query = "INSERT INTO target (nick,pid,tick,round,uid) VALUES (%s,%s,%s,%s,%s)"
        try:
            self.cursor.execute(query, (irc_msg.nick, p.id, tick, irc_msg.round, uid,))
            if uid:
                reply = "Booked landing on %s:%s:%s tick %s for user %s" % (
                    p.x,
                    p.y,
                    p.z,
                    tick,
                    irc_msg.user,
                )
            else:
                reply = "Booked landing on %s:%s:%s tick %s for nick %s" % (
                    p.x,
                    p.y,
                    p.z,
                    tick,
                    irc_msg.nick,
                )
        except psycopg2.IntegrityError:
            query = "SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid, t2.pnick AS pnick, t2.userlevel AS userlevel "
            query += " FROM target AS t1 LEFT JOIN user_list AS t2 ON t1.uid=t2.id "
            query += " WHERE t1.pid=%s AND t1.tick=%s AND t1.round=%s"

            self.cursor.execute(query, (p.id, tick, irc_msg.round,))
            book = self.cursor.fetchone()
            if not book:
                raise Exception(
                    "Integrity error? Unable to booking for pid %s and tick %s"
                    % (p.id, tick)
                )
            if book["pnick"]:
                reply = (
                    "Target %s:%s:%s is already booked for landing tick %s by user %s"
                    % (p.x, p.y, p.z, book["tick"], book["pnick"])
                )
            else:
                reply = (
                    "Target %s:%s:%s is already booked for landing tick %s by nick %s"
                    % (p.x, p.y, p.z, book["tick"], book["nick"])
                )
        except BaseException:
            raise

        irc_msg.reply(reply)

        return 1
