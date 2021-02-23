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

import re
from munin import loadable


class adduser(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1000)
        self.paramre = re.compile(r"^\s*(\S+)\s+(\d+)(\s+(\S+))?")
        self.usage = (
            self.__class__.__name__ + " <pnick>[,<pnick2>[...]] <level> [sponsor]"
        )

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        u = self.load_user(user, irc_msg)
        if not u:
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply(self.usage)
            return 0

        pnicks = m.group(1).lower()
        access_lvl = int(m.group(2))

        if m.group(4):
            sponsor_user = self.load_user_from_pnick(m.group(4), irc_msg.round)
            if not sponsor_user or sponsor_user.userlevel < 100:
                irc_msg.reply(
                    f"Nice try wiseass, but you can't pass the buck on to {m.group(4)}, they're not a member"
                )
                return 0
            sponsor = sponsor_user.pnick
        else:
            sponsor = u.pnick

        if access_lvl >= access:
            irc_msg.reply(
                "You may not add a user with equal or higher access to your own"
            )
            return 0

        added = []
        exists = []
        botnick = self.config.get('Connection', 'nick')
        for pnick in pnicks.split(","):
            if not pnick:
                continue
            if pnick.lower() == botnick.lower():
                irc_msg.reply("You can't add %s, that's me, you prick!" % (botnick,))
            else:
                gimp = self.load_user_from_pnick(pnick, irc_msg.round)
                query = None
                if not gimp or pnick.lower() not in [ x.lower() for x in [ gimp.pnick, gimp.alias_nick ] if x is not None ]:
                    query = "INSERT INTO user_list (userlevel,sponsor,pnick) VALUES (%s,%s,%s)"
                elif gimp.userlevel < access_lvl:
                    query = "UPDATE user_list SET userlevel = %s, sponsor=%s WHERE pnick ilike %s"
                if query:
                    self.cursor.execute(query, (access_lvl, sponsor, pnick,))
                    added.append(pnick)
                else:
                    exists.append(pnick)
        if len(added):
            irc_msg.reply(
                "Added users (%s) at level %s" % (",".join(added), access_lvl)
            )
            irc_msg.client.privmsg(
                "P",
                "adduser #%s %s 399"
                % (self.config.get("Auth", "home"), ",".join(added),),
            )
            for nick in added:
                irc_msg.client.privmsg(
                    "P",
                    "modinfo #%s automode %s op"
                    % (self.config.get("Auth", "home"), nick,),
                )
        if len(exists):
            irc_msg.reply("Users (%s) already exist" % (",".join(exists),))
        return 1
