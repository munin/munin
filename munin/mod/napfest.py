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
        super(self.__class__, self).__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*")
        self.usage = self.__class__.__name__
        self.war_start_re = re.compile(r"(.*) has declared war on (.*) !")
        self.nap_start_re = re.compile(r"(.*) and (.*) have confirmed they have formed a non-aggression pact.")
        self.nap_end_re = re.compile(r"(.*) has decided to end its NAP with (.*).")
        self.ally_start_re = re.compile(r"(.*) and (.*) have confirmed they are allied.")
        self.ally_end_re = re.compile(r"(.*) has decided to end its alliance with (.*).")
        self.helptext = ['Lists the most recent 10 alliance relation changes']

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.match(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        war_duration = self.config.getint('Planetarion', 'war_duration')

        query = "SELECT tick, text FROM userfeed_dump"
        query += " WHERE type = 'Relation Change'"
        query += " AND round = %s"
        query += " AND text NOT ILIKE %s"
        query += " ORDER BY tick DESC"
        query += " LIMIT 10"
        self.cursor.execute(query, (irc_msg.round, "%'s war with % has expired.",))

        if self.cursor.rowcount == 0:
            reply = 'Nothing has happened yet, go fight some fools!'
        else:
            events = []
            for row in self.cursor.dictfetchall():
                m = self.war_start_re.match(row['text'])
                if m:
                    events.append('pt%d-%d: War between %s and %s' % (
                        row['tick'],
                        war_duration + row['tick'],
                        m.group(1),
                        m.group(2)))
                if not m:
                    m = self.nap_start_re.match(row['text'])
                    if m:
                        events.append('pt%d: %s NAPed %s' % (
                            row['tick'],
                            m.group(1),
                            m.group(2)))
                if not m:
                    m = self.nap_end_re.match(row['text'])
                    if m:
                        events.append('pt%d: %s ended its NAP with %s' % (
                            row['tick'],
                            m.group(1),
                            m.group(2)))
                if not m:
                    m = self.ally_start_re.match(row['text'])
                    if m:
                        events.append('pt%d: %s allied %s' % (
                            row['tick'],
                            m.group(1),
                            m.group(2)))
                if not m:
                    m = self.ally_end_re.match(row['text'])
                    if m:
                        events.append('pt%d: %s ended its alliance with %s' % (
                            row['tick'],
                            m.group(1),
                            m.group(2)))
                if not m:
                    reply = "What the hell happened at pt%d? %s? Fuck that." % (
                        row['tick'],
                        row['text'])
                    break

                reply = 'Most recent 10 alliance relation changes: %s' % (' | '.join(reversed(events)))
        irc_msg.reply(reply)
        return 1
