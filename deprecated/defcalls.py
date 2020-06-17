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

# This module doesn't have anything alliance specific as far as I can tell.
# qebab, 24/6/08.

import re
import string
from munin import loadable


class defcalls(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.commandre = re.compile(r"^" + self.__class__.__name__ + "(.*)")
        self.paramre = re.compile(r"^(\s+(\S+))?")

        self.usage = self.__class__.__name__ + " <eta|status>"
        self.helptext = [
            "Show defense calls",
            "Valid statuses include covered, uncovered, recheck, impossible, invalid, semicovered, recall and fake.",
        ]

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        defcall_type = m.group(2)

        if defcall_type == None:
            return self.reply_all_defcalls(nick, user, access)
        else:
            return self.reply_typed_defcalls(nick, defcall_type, user, access)

    def reply_typed_defcalls(self, defcall_type, user, access):
        query = "SELECT t2.status,count(*) AS count FROM defcalls AS t1"
        query += " INNER JOIN defcall_status AS t2"
        query += " ON t1.status=t2.id"
        query += " WHERE t1.landing_tick >  (SELECT max_tick())"
        query += " AND t2.status ilike %s"
        query += " GROUP BY t2.status"

        args = (defcall_type + "%",)

        self.cursor.execute(query, args)

        reply = ""
        if self.cursor.rowcount < 1:
            irc_msg.reply(
                "No active defcalls matching '%s' at the moment. Seriously."
                % (defcall_type,)
            )
            return 1
        c = self.cursor.fetchone()
        reply += "Status '%s' shows %s calls:" % (c["status"], c["count"])

        current_tick = self.current_tick()

        query = "SELECT t1.id AS id,t1.landing_tick AS landing_tick,t2.x AS x,t2.y AS y,t2.z AS z"
        query += " FROM defcalls AS t1"
        query += " INNER JOIN planet_dump AS t2 ON t1.target=t2.id"
        query += " INNER JOIN defcall_status AS t3 ON t1.status=t3.id"
        query += " WHERE t2.tick=(SELECT max_tick())"
        query += " AND t1.landing_tick > (SELECT max_tick())"
        query += " AND t3.status ilike %s"

        self.cursor.execute(query, args)

        calls = self.cursor.fetchall()
        a = []
        for d in calls:
            a.append(
                "%s:%s:%s (id: %s, eta: %s)"
                % (d["x"], d["y"], d["z"], d["id"], d["landing_tick"] - current_tick)
            )
        reply += " " + string.join(a, " | ")

        irc_msg.reply(reply)

        return 1

    def reply_all_defcalls(self, user, access):
        query = "SELECT t2.status,count(*) AS count FROM defcalls AS t1"
        query += " INNER JOIN defcall_status AS t2"
        query += " ON t1.status=t2.id"
        query += " WHERE t1.landing_tick >  (SELECT max_tick())"
        query += " GROUP BY t2.status"

        self.cursor.execute(query)

        if self.cursor.rowcount < 1:
            irc_msg.reply("No active defcalls at the moment. Seriously.")
            return 1

        total_calls = 0
        reply = ""
        calls = self.cursor.fetchall()
        a = []
        for d in calls:
            total_calls += d["count"]
            a.append("%s: %s" % (d["status"], d["count"]))
        reply += "Active calls: %d |" % (total_calls,)
        reply += " " + string.join(a, " ")
        print a
        irc_msg.reply(reply)

        return 1
