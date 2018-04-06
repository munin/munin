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
import munin.loadable as loadable


class gac(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(.*)")
        self.usage = self.__class__.__name__ + ""
        self.helptext = [
            'Displays stats about the Gross Alliance Cookies. Similar to the Gross Domestic Product, GAC covers how many %s cookies changed hands in a given week.' %
            (self.config.get(
                'Auth',
                'alliance'),
             )]

    def execute(self, user, access, irc_msg):
        m = self.commandre.search(irc_msg.command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        last_5_gac = self.get_last_5_gac()

        max_gac = self.get_max_gac()
        min_gac = self.get_min_gac()
        reply = "Gross Alliance Cookies for %s for last 5 weeks (current first): %s" % (
            self.config.get('Auth', 'alliance'), ', '.join(last_5_gac))
        reply += " | Highest ever GAC: %s in week %s/%s." % (
            max_gac['gac'], max_gac['week_number'], max_gac['year_number'])
        reply += " | Lowest ever GAC: %s in week %s/%s." % (min_gac['gac'],
                                                            min_gac['week_number'], min_gac['year_number'])
        irc_msg.reply(reply)
        return 1

    def get_max_gac(self):
        return self.get_minmax_gac(max=True)

    def get_min_gac(self):
        return self.get_minmax_gac(min=True)

    def get_minmax_gac(self, max=True, min=False):
        if min:
            order = "ASC"
        elif max:
            order = "DESC"
        query = "SELECT sum(howmany) AS gac,year_number, week_number"
        query += " FROM cookie_log"
        query += " GROUP BY year_number, week_number"
        query += " ORDER BY sum(howmany) %s" % (order,)
        query += " LIMIT 1"
        self.cursor.execute(query)
        print(self.cursor.rowcount)
        return self.cursor.dictfetchone()

    def get_last_5_gac(self):
        query = "SELECT sum(howmany) AS gac, week_number"
        query += " FROM cookie_log"
        query += " GROUP BY year_number, week_number"
        query += " ORDER BY year_number DESC, week_number DESC"
        query += " LIMIT 5"
        self.cursor.execute(query)
        return [str(x['gac']) for x in self.cursor.dictfetchall()]
