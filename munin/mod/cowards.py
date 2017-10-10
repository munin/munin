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
        super(self.__class__, self).__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(.+)")
        self.usage = self.__class__.__name__ + ' <alliance>'
        self.helptext = ['Lists the currently active relations for the given alliance']

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
            reply = '%s is neutral. Easy targets!' % (a.name)
        else:
            alliances = []
            naps = []
            wars = []
            for row in self.cursor.dictfetchall():
                if row['type'] == 'Ally':
                    if a.name == row['initiator']:
                        alliances.append(row['acceptor'])
                    else:
                        alliances.append(row['initiator'])
                elif row['type'] == 'NAP':
                    if a.name == row['initiator']:
                        naps.append(row['acceptor'])
                    else:
                        naps.append(row['initiator'])
                elif row['type'] == 'War':
                    if a.name == row['initiator']:
                        wars.append("%s (until pt%d)" % (row['acceptor'], row['end_tick']))
                    else:
                        wars.append("%s (until pt%d)" % (row['initiator'], row['end_tick']))

            # <alliance> is allied with: X, Y, Z | <alliance> has a NAP with A, B, C | <alliance> is at war with: H
            # <alliance> is not allied with anyone | <alliance> does not have any NAPs | <alliance> is not at war with anyone
            reply = a.name
            if len(alliances) == 0:
                reply += ' is not allied with anyone'
            else:
                reply += ' is allied with ' + ', '.join(alliances)
            reply += ' | ' + a.name
            if len(naps) == 0:
                reply += ' does not have any NAPs'
            else:
                reply += ' has NAPs with ' + ', '.join(naps)
            reply += ' | ' + a.name
            if len(wars) == 0:
                reply += ' is not at war with anyone'
            else:
                reply += ' is at war with ' + ', '.join(wars)
        irc_msg.reply(reply)
        return 1
