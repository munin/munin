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


class votestatus(loadable.loadable):
    """ 
    foo 
    """

    def __init__(self, client, conn, cursor):
        loadable.loadable.__init__(self, client, conn, cursor, 100)
        self.commandre = re.compile(r"^" + self.__class__.__name__ + "(.*)")
        self.paramre = re.compile(r"^\s+(\S+)")
        self.usage = self.__class__.__name__ + "[<nick>]"
        self.helptext = [
            "This command either shows the list of nicks currently being voted to be kicked from the alliance or, if given a nick, it will show the people currently voting for that nick to be kicked (ie a list of cunts)"
        ]

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

        # assign param variables

        m = self.paramre.search(m.group(1))

        # do stuff here
        if m:
            search = m.group(1)

            idiot = loadable.user(pnick=search)
            if not idiot.load_from_db(self.conn, self.client, self.cursor):
                self.client.reply(
                    prefix,
                    nick,
                    target,
                    "That idiot doesn't exist, if anyone wants to fix you being an idiot they can kickvote %s"
                    % (user,),
                )
                return 1

            query = "SELECT t2.pnick FROM kickvote AS t1"
            query += " INNER JOIN user_list AS t2 ON voter=t2.id"
            query += " INNER JOIN user_list AS t3 ON moron=t3.id"
            query += " WHERE t3.pnick ilike %s "

            self.cursor.execute(query, (idiot.pnick,))

            reply = "The following users have voted to kick %s:" % (idiot.pnick,)

            prev = []
            for r in self.cursor.fetchall():
                prev.append("%s" % (r["pnick"],))
                pass
            reply += " " + string.join(prev, ", ")
            pass

        else:
            query = "SELECT DISTINCT pnick FROM kickvote AS t1"
            query += " INNER JOIN user_list AS t2 ON moron=t2.id"

            self.cursor.execute(query, ())

            reply = "The following idiots are considered for a kick:"
            prev = []
            for r in self.cursor.fetchall():
                prev.append("%s" % (r["pnick"],))
                pass
            reply += " " + string.join(prev, ", ")
            pass
        self.client.reply(prefix, nick, target, reply)
