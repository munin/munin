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

# Nothing alliance specific in here as far as I can tell.
# qebab, 24/6/08.

import re
from munin import loadable


class info(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 50)
        self.paramre = re.compile(r"^\s*(.+)")
        self.usage = (
            self.__class__.__name__
            + " [alliance] (All information taken from intel, for tag information use the lookup command)"
        )

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        alliance = m.group(1)
        query = self.query_for_info()
        args = (
            irc_msg.round,
            irc_msg.round,
            "%" + alliance + "%",
            "%" + alliance + "%",
        )
        self.cursor.execute(query, args)
        reply = ""
        if self.cursor.rowcount < 1:
            irc_msg.reply("Nothing in intel matches your search '%s'" % (alliance,))
        else:
            res = self.cursor.fetchone()
            irc_msg.reply(self.format_result(alliance, res, counting=False))

            counting_members = self.config.getint("Planetarion", "counting_tag_members")
            if res["members"] > counting_members:
                query = self.query_for_info_limit()
                args = (
                    irc_msg.round,
                    irc_msg.round,
                    "%" + alliance + "%",
                    counting_members,
                    "%" + alliance + "%",
                )
                self.cursor.execute(query, args)
                res = self.cursor.fetchone()
                irc_msg.reply(self.format_result(alliance, res, counting=True))
        return 1

    def query_for_info_limit(self):
        query = "SELECT count(*) AS members, min(t.name) AS alliance, sum(t.value) AS tot_value, sum(t.score) AS tot_score, sum(t.size) AS tot_size, sum(t.xp) AS tot_xp"
        query += " FROM (SELECT p.value AS value, p.score AS score, p.size AS size, p.xp AS xp, a.name AS name"
        query += " FROM planet_dump AS p"
        query += " INNER JOIN intel AS i ON p.id=i.pid"
        query += " LEFT JOIN alliance_canon AS a ON i.alliance_id=a.id"
        query += " WHERE p.tick=(SELECT max_tick(%s::smallint)) AND p.round=%s AND a.name ILIKE %s ORDER BY p.score DESC LIMIT %s) AS t"
        query += " GROUP BY t.name ILIKE %s"
        return query

    def query_for_info(self):
        query = "SELECT count(*) AS members, min(a.name) AS alliance, sum(p.value) AS tot_value, sum(p.score) AS tot_score, sum(p.size) AS tot_size, sum(p.xp) AS tot_xp"
        query += " FROM planet_dump AS p"
        query += " INNER JOIN intel AS i ON p.id=i.pid"
        query += " LEFT JOIN alliance_canon a ON i.alliance_id=a.id"
        query += " WHERE p.tick=(SELECT max_tick(%s::smallint)) AND p.round=%s AND a.name ILIKE %s"
        query += " GROUP BY a.name ILIKE %s"
        return query

    def format_result(self, alliance, res, counting):
        reply = "%s %sMembers: %s | Value: %s (Avg: %s) |" % (
            res['alliance'],
            "Counting " if counting else "",
            res["members"],
            self.format_real_value(res["tot_value"]),
            self.format_real_value(res["tot_value"] / res["members"]),
        )
        reply += " Score: %s (Avg: %s) |" % (
            self.format_real_value(res["tot_score"]),
            self.format_real_value(res["tot_score"] / res["members"]),
        )
        reply += " Size: %s, Avg(%s) | XP: %s (Avg: %s)" % (
            res["tot_size"],
            round(res["tot_size"] / res["members"]),
            res["tot_xp"],
            round(res["tot_xp"] / res["members"]),
        )
        return reply
