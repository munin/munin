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


class napfest(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*")
        self.usage = self.__class__.__name__
        self.war_start_re = re.compile(r"(.*) has declared war on (.*) !")
        self.auto_war_start_re = re.compile(
            r"(.*) has automatically declared war on (.*) due to long-standing aggression !"
        )
        self.nap_start_re = re.compile(
            r"(.*) and (.*) have confirmed they have formed a non-aggression pact."
        )
        self.nap_end_re = re.compile(r"(.*) has decided to end its NAP with (.*).")
        self.ally_start_re = re.compile(
            r"(.*) and (.*) have confirmed they are allied."
        )
        self.ally_end_re = re.compile(
            r"(.*) has decided to end its alliance with (.*)."
        )
        self.helptext = ["List the most recent 10 alliance relation changes"]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.match(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        war_duration = self.config.getint("Planetarion", "war_duration")
        auto_war_duration = self.config.getint("Planetarion", "auto_war_duration")

        # This number of alliance relation changes should fit neatly in 1
        # message.
        limit = 9
        query = "SELECT tick, text FROM userfeed_dump"
        query += " WHERE type = 'Relation Change'"
        query += " AND round = %s"
        query += " AND text NOT ILIKE %s"
        query += " ORDER BY tick DESC"
        query += " LIMIT %s"
        args = (
            irc_msg.round,
            "%'s war with % has expired.",
            limit
        )
        self.cursor.execute(query, args)

        if self.cursor.rowcount == 0:
            reply = "Nothing has happened yet, go fight some fools!"
        else:
            events = []
            for row in self.cursor.fetchall():
                m = self.war_start_re.match(row["text"])
                if m:
                    events.append(
                        "pt%d-%d: War by %s against %s"
                        % (
                            row["tick"],
                            war_duration + row["tick"],
                            m.group(1),
                            m.group(2),
                        )
                    )
                if not m:
                    m = self.auto_war_start_re.match(row["text"])
                    if m:
                        events.append(
                            "pt%d-%d: Auto-war by %s against %s"
                            % (
                                row["tick"],
                                auto_war_duration + row["tick"],
                                m.group(1),
                                m.group(2),
                            )
                        )
                if not m:
                    m = self.nap_start_re.match(row["text"])
                    if m:
                        events.append(
                            "pt%d: %s NAPed %s" % (row["tick"], m.group(1), m.group(2))
                        )
                if not m:
                    m = self.nap_end_re.match(row["text"])
                    if m:
                        events.append(
                            "pt%d: %s unNAPed %s"
                            % (row["tick"], m.group(1), m.group(2))
                        )
                if not m:
                    m = self.ally_start_re.match(row["text"])
                    if m:
                        events.append(
                            "pt%d: %s allied %s" % (row["tick"], m.group(1), m.group(2))
                        )
                if not m:
                    m = self.ally_end_re.match(row["text"])
                    if m:
                        events.append(
                            "pt%d: %s unallied %s"
                            % (row["tick"], m.group(1), m.group(2))
                        )
                if not m:
                    events.append(
                        "pt%d: What the hell!? %s? Fuck that"
                        % (row["tick"], row["text"],)
                    )

            reply = "Most recent %s alliance relation changes: %s" % (
                limit,
                " | ".join(reversed(events))
            )
        irc_msg.reply(reply)
        return 1
