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

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08
# I lied. Removed alliance specific things.
# qebab, 24/6/08.

import re
from munin import loadable


class loosecunts(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^(\s*(\S+))?")
        self.usage = self.__class__.__name__ + " [alliance]"
        self.helptext = [
            'Find the planets with the smallest score gains over the last 72 ticks'
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        search = irc_msg.user_or_nick()
        m = self.paramre.search(irc_msg.command_parameters)
        alliance = m.group(2) if m else None

        for q in [
            "DROP TABLE epenis",
            "DROP SEQUENCE xp_gain_rank",
            "DROP SEQUENCE value_diff_rank",
            "DROP SEQUENCE activity_rank",
        ]:
            try:
                self.cursor.execute(q)
            except Exception:
                pass

        query = "CREATE TEMP SEQUENCE xp_gain_rank;CREATE TEMP SEQUENCE value_diff_rank;CREATE TEMP SEQUENCE activity_rank"
        self.cursor.execute(query)
        query = "SELECT setval('xp_gain_rank',1,false); SELECT setval('value_diff_rank',1,false); SELECT setval('activity_rank',1,false)"
        self.cursor.execute(query)

        query = """
        CREATE TEMP TABLE epenis AS
        (SELECT *,nextval('activity_rank') AS activity_rank
         FROM (SELECT *,nextval('value_diff_rank') AS value_diff_rank
               FROM (SELECT *,nextval('xp_gain_rank') AS xp_gain_rank
                     FROM (SELECT p0.x,p0.y,p0.z, i.nick, ac.name AS alliance, p0.xp-p72.xp AS xp_gain, p0.score-p72.score AS activity, p0.value-p72.value AS value_diff
                           FROM       planet_dump     AS p0
                           LEFT JOIN  intel           AS i   ON p0.id=i.pid
                           LEFT JOIN  alliance_canon  AS ac  ON i.alliance_id=ac.id
                           INNER JOIN planet_dump     AS p72 ON p0.id=p72.id AND p0.tick - 72 = p72.tick
                           WHERE p0.tick = (SELECT max_tick(%s::smallint)) AND p0.round = %s
        """
        args = (
            irc_msg.round,
            irc_msg.round,
        )
        if alliance is not None:
            query += "                    AND ac.name ILIKE %s"
            args += ("%%%s%%" % (alliance,),)
        query += """
                           ORDER BY xp_gain DESC) AS t6
                     ORDER BY value_diff DESC) AS t7
               ORDER BY activity DESC) AS t8)
        """
        self.cursor.execute(query,
                            args)

        query = (
            "SELECT x || ':' || y || ':' || z AS coords,nick,alliance,activity,activity_rank"
            " FROM epenis"
            " ORDER BY activity_rank DESC LIMIT 5"
        )
        self.cursor.execute(query, ())

        if self.cursor.rowcount < 1:
            self.cursor.execute("SELECT max_tick(%s::smallint)", (irc_msg.round,))
            if self.cursor.fetchone()['max_tick'] < 73:
                irc_msg.reply("There is no penis before tick 73")
            else:
                irc_msg.reply("The penis isn't small! IT'S CLOAKED!")
            return 1

        prev = []
        for b in self.cursor.fetchall():
            prev.append(
                "%d:%s%s (%s)"
                % (
                    b["activity_rank"],
                    b["nick"] or "[%s]" % (b["coords"],),
                    "/%s" % (b["alliance"],) if "alliance" in b else "",
                    self.format_value(b["activity"] * 100),
                )
            )
        reply = "Loose cunts: %s" % (", ".join(prev))

        irc_msg.reply(reply)
        return 1
