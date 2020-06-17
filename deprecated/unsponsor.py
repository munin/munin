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

# Nothing ascendancy/jester specific found in this module.
# qebab, 24/6/08.


class unsponsor(loadable.loadable):
    def __init__(self, client, conn, cursor):
        loadable.loadable.__init__(self, client, conn, cursor, 1000)
        self.commandre = re.compile(r"^" + self.__class__.__name__ + "(.*)")
        self.paramre = re.compile(r"^\s*(\S+)")
        self.usage = self.__class__.__name__ + "<pnick>"

    def execute(self, nick, username, host, target, prefix, command, user, access):
        m = self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(
                prefix,
                nick,
                target,
                "You do not have enough access to use this command",
            )
            return 0
        if not user:
            self.client.reply(
                prefix,
                nick,
                target,
                "You must be registered to use the "
                + self.__class__.__name__
                + " command (log in with P and set mode +x)",
            )

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            self.client.reply(prefix, nick, target, "Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        recruit = m.group(1)

        # do stuff here

        query = (
            "SELECT * FROM unsponsor(%s,%s)"  # AS t1(success BOOLEAN, retmessage TEXT)"
        )
        self.cursor.execute(query, (user, recruit))

        res = self.cursor.fetchone()

        if res["success"]:
            reply = "You have unsponsored '%s'. " % (recruit,)
        else:
            reply = "You may not unsponsor '%s'. Reason: %s" % (
                recruit,
                res["retmessage"],
            )
        self.client.reply(prefix, nick, target, reply)

        return 1
