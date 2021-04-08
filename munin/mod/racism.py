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


class racism(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 50)
        self.paramre = re.compile(r"^\s*(\S+)")
        self.usage = (
            self.__class__.__name__
            + " <alliance> (All information taken from intel, for tag information use the lookup command)"
        )
        self.helptext = [
            "Shows averages for each race matching a given alliance in intel."
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        alliance_string = m.group(1)
        alliance = loadable.alliance(name=alliance_string)
        if alliance.load_most_recent(self.cursor, irc_msg.round):
            query = (
                "SELECT count(*) AS members, sum(p.value) AS tot_value, sum(p.score) AS tot_score,"
                "       sum(p.size) AS tot_size, sum(p.xp) AS tot_xp, p.race AS race"
                " FROM       planet_dump AS p"
                " INNER JOIN intel       AS i ON p.id=i.pid"
                " WHERE i.alliance_id = %s"
                " AND   p.tick = (SELECT max_tick(%s::smallint))"
                " GROUP BY p.race"
                " ORDER BY array_position(array['Ter','Cat','Xan','Zik','Etd'], p.race::text) ASC"
            )
            self.cursor.execute(
                query,
                (
                    alliance.id,
                    irc_msg.round,
                ),
            )
            if self.cursor.rowcount > 0:
                results = self.cursor.fetchall()
                irc_msg.reply("Demographics for %s: %s" % (
                    alliance.name,
                    " | ".join([self.profile(r) for r in results]),))
                return 1
            else:
                irc_msg.reply("Nothing in intel matches your search '%s'" % (alliance_string,))
        else:
            irc_msg.reply("No alliance matching '%s' found" % (alliance_string))
        return 0

    def profile(self, res):
        return "%s %s Val(%s) Score(%s) Size(%s) XP(%s)" % (
            res["members"],
            res["race"],
            self.format_real_value(res["tot_value"] / res["members"]),
            self.format_real_value(res["tot_score"] / res["members"]),
            self.format_real_value(res["tot_size"] / res["members"]),
            self.format_real_value(res["tot_xp"] / res["members"]),
        )
