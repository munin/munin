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

from munin import loadable


class tryhards(loadable.loadable):
    """
    Show top 5s
    """

    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(\S+)\s*(\S+)")
        self.usage = (
            self.__class__.__name__
            + " <alliances|galaxy|planet> [score|total_score|value|xp|size]"
        )
        self.helptext = [
            "Shows top5 for alliances, galaxies or planets ranked by score, total_score, value, xp or size"
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
            return self.reply_usage(irc_msg)
        p1 = m.group(1).lower()
        p2 = m.group(2).lower()

        a = ["alliances", "galaxy", "galaxies", "planets"]

        if p2 in "score":
            p2 = "score"
        elif p2 in "total_score":
            p2 = "total_score"
        elif p2 in "value":
            p2 = "value"
        elif p2 in "xp":
            p2 = "xp"
        elif p2 in "size":
            p2 = "size"
        else:
            return self.reply_usage(irc_msg)

        if p1 in "alliances":
            if p2 in "xp":
                return self.reply_usage(irc_msg)
            self.rank_alliance_by(p2, irc_msg)
        elif p1 in "planets":
            p1 = "planet"
            self.rank_planet_by(p2, irc_msg)
        elif p1 in "galaxy" or p1 in "galaxies":
            p1 = "galaxy"
            self.rank_galaxy_by(p2, irc_msg)
        else:
            return self.reply_usage(irc_msg)

    def reply_usage(self, irc_msg):
        irc_msg.reply("Usage: %s" % (self.usage,))
        return 0

    def rank_alliance_by(self, qualifier, irc_msg):
        if qualifier in "value":
            ranker = "total_value"
        else:
            ranker = qualifier
        rank = "%s_rank" % (ranker,)
        query = "SELECT name,%s,%s" % (ranker, rank)
        query += " FROM alliance_dump"
        query += " WHERE tick=(SELECT max_tick(%s::smallint)) AND round=%s"
        query += " ORDER BY %s ASC" % (rank,)
        query += " LIMIT 5"
        self.cursor.execute(query, (irc_msg.round, irc_msg.round,))
        if self.cursor.rowcount < 1:
            irc_msg.reply("lol")

        reply = "Alliances trying too hard for %s: " % (ranker.replace("_", " "),)
        reply += ", ".join(
            [
                "%s: %s (%s)" % (x[rank], x["name"], self.format_real_value(x[ranker]))
                for x in self.cursor.fetchall()
            ]
        )
        irc_msg.reply(reply)

    def rank_galaxy_by(self, qualifier, irc_msg):
        rank = "%s_rank" % (qualifier,)
        if "total" in qualifier:
            return self.reply_usage(irc_msg)
        query = "SELECT x,y,name,%s,%s" % (qualifier, rank)
        query += " FROM galaxy_dump"
        query += " WHERE tick=(SELECT max_tick(%s::smallint)) AND round=%s"
        query += " ORDER BY %s ASC" % (rank,)
        query += " LIMIT 5"
        self.cursor.execute(query, (irc_msg.round, irc_msg.round,))
        if self.cursor.rowcount < 1:
            irc_msg.reply("lol")

        reply = "Galaxies trying too hard for %s: " % (qualifier.replace("_", " "),)
        reply += ", ".join(
            [
                "%s: %s:%s - %s (%s)"
                % (
                    x[rank],
                    x["x"],
                    x["y"],
                    x["name"],
                    self.format_real_value(x[qualifier]),
                )
                for x in self.cursor.fetchall()
            ]
        )
        irc_msg.reply(reply)

    def rank_planet_by(self, qualifier, irc_msg):
        rank = "%s_rank" % (qualifier,)
        if "total" in qualifier:
            return self.reply_usage(irc_msg)
        query = "SELECT p1.x,p1.y,p1.z,p1.%s,p1.%s,p2.nick,p3.name" % (qualifier, rank)
        query += " FROM planet_dump p1"
        query += " LEFT JOIN intel p2 ON p2.pid=p1.id"
        query += " LEFT JOIN alliance_canon p3 ON p3.id=p2.alliance_id"
        query += " WHERE p1.tick=(SELECT max_tick(%s::smallint)) AND p1.round=%s"
        query += " ORDER BY %s ASC" % (rank,)
        query += " LIMIT 5"
        self.cursor.execute(query, (irc_msg.round, irc_msg.round,))
        if self.cursor.rowcount < 1:
            irc_msg.reply("lol")

        reply = "Planets trying too hard for %s: " % (qualifier,)
        reply += ", ".join(
            [
                "%s: %s:%s:%s (%s/%s) (%s)"
                % (
                    x[rank],
                    x["x"],
                    x["y"],
                    x["z"],
                    x["nick"],
                    x["name"],
                    self.format_real_value(x[qualifier]),
                )
                for x in self.cursor.fetchall()
            ]
        )
        irc_msg.reply(reply)
