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


class cowards(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(.+)")
        self.usage = self.__class__.__name__ + " <alliance>"
        self.helptext = ["Lists the currently active relations for the given alliance"]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.match(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        alliance_name = m.group(1)
        a = loadable.alliance(name=alliance_name)
        if not a.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply("No alliance matching '%s' found" % (alliance_name))
            return 0

        query = "SELECT rel.type, rel.end_tick, canon1.name AS initiator, canon2.name AS acceptor"
        query += " FROM alliance_relation AS rel"
        query += " INNER JOIN alliance_canon AS canon1 ON rel.initiator = canon1.id"
        query += " INNER JOIN alliance_canon AS canon2 ON rel.acceptor = canon2.id"
        query += " WHERE ( canon1.id = %s OR canon2.id = %s )"
        query += " AND rel.end_tick > (SELECT max_tick(%s::smallint))"
        self.cursor.execute(query, (a.id, a.id, irc_msg.round))

        if self.cursor.rowcount == 0:
            reply = "%s is neutral. Easy targets!" % (a.name)
        else:
            alliances = []
            naps = []
            wars = []
            auto_wars = []
            for row in self.cursor.fetchall():
                if row["type"] == "Ally":
                    if a.name == row["initiator"]:
                        alliances.append(row["acceptor"])
                    else:
                        alliances.append(row["initiator"])
                elif row["type"] == "NAP":
                    if a.name == row["initiator"]:
                        naps.append(row["acceptor"])
                    else:
                        naps.append(row["initiator"])
                elif row["type"] == "War":
                    # Wars are one-way.
                    if a.name == row["initiator"]:
                        wars.append(
                            "%s (until pt%d)" % (row["acceptor"], row["end_tick"])
                        )
                elif row["type"] == "Auto-War":
                    # Auto-Wars are also one-way.
                    if a.name == row["initiator"]:
                        auto_wars.append(
                            "%s (until pt%d)" % (row["acceptor"], row["end_tick"])
                        )

            lines = []
            if len(alliances) > 0:
                lines.append("%s is allied with: %s" % (a.name, ", ".join(alliances),))
            if len(naps) > 0:
                lines.append("%s has NAPs with: %s" % (a.name, ", ".join(naps),))
            if len(wars) > 0:
                lines.append("%s is at war with: %s" % (a.name, ", ".join(wars),))
            if len(auto_wars) > 0:
                lines.append("%s has auto-wars with: %s" % (a.name, ", ".join(auto_wars),))
        irc_msg.reply(' | '.join(lines))
        return 1
