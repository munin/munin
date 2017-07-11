"""
Loadable subclass
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

from psycopg2 import psycopg1 as psycopg
import re
from munin import loadable


class adduser(loadable.loadable):
    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 1000)
        self.paramre = re.compile(r"^\s+(\S+)\s+(\d+)")
        self.usage = self.__class__.__name__ + " <pnick>[,<pnick2>[...]] <level>"

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        u = self.load_user(user, irc_msg)
        if not u:
            return 0

        m = self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: adduser <pnick>[,<pnick2>[...]] <level>")
            return 0

        pnicks = m.group(1).lower()
        access_lvl = int(m.group(2))

        if access_lvl >= access:
            irc_msg.reply("You may not add a user with equal or higher access to your own")
            return 0

        added = []
        exists = []
        for pnick in pnicks.split(","):
            if not pnick:
                continue
            gimp = self.load_user_from_pnick(pnick, irc_msg.round)
            if not gimp or gimp.pnick.lower() != pnick.lower() or gimp.userlevel < access_lvl:
                if not gimp or gimp.pnick.lower() != pnick.lower():
                    query = "INSERT INTO user_list (userlevel,sponsor,pnick) VALUES (%s,%s,%s)"
                elif gimp.userlevel < access_lvl:
                    query = "UPDATE user_list SET userlevel = %s, sponsor=%s WHERE pnick ilike %s"
                self.cursor.execute(query, (access_lvl, u.pnick, pnick))
                added.append(pnick)
            else:
                exists.append(pnick)
        if len(added):
            irc_msg.reply("Added users (%s) at level %s" % (",".join(added), access_lvl))
            irc_msg.client.privmsg('P', "adduser #%s %s 399" % (self.config.get('Auth', 'home'), ",".join(added),))
            for nick in added:
                irc_msg.client.privmsg('P', "modinfo #%s automode %s op" % (self.config.get('Auth', 'home'), nick,))
        if len(exists):
            irc_msg.reply("Users (%s) already exist" % (",".join(exists),))

        return 1
