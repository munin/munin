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


# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08


class add(loadable.loadable):
    def __init__(self, client, conn, cursor):
        loadable.loadable.__init__(self, client, conn, cursor, 100)
        self.commandre = re.compile(r"^" + self.__class__.__name__ + "(\s+.*)")
        self.paramre = re.compile(r"^\s+(\d+)[. :-](\d+)[. :-](\d+)\s+(\S+)(\s+(\S+))?")
        self.usage = self.__class__.__name__ + " <x:y:z> <alliance> [nick]"

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

        m = self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix, nick, target, "Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        alliance_name = m.group(4)
        person_nick = m.group(6)

        p = loadable.planet(x=x, y=y, z=z)

        if not p.load_most_recent(self.conn, self.client, self.cursor):
            self.client.reply(
                prefix,
                nick,
                target,
                "No planet matching '%s:%s:%s' found" % (p.x, p.y, p.z,),
            )
            return 1

        i = loadable.intel(pid=p.id)
        if not i.load_from_db(self.conn, self.client, self.cursor):
            pass

        if i.id > 0:
            args = (alliance_name,)
            query = "UPDATE intel SET alliance=%s"
            if person_nick:
                args += (person_nick,)
                query += ",nick=%s"
            args += (i.id,)
            query += " WHERE id=%s"
            self.cursor.execute(query, args)
        else:
            args = (
                p.id,
                alliance_name,
            )
            query = "INSERT INTO intel (pid,alliance"
            if person_nick:
                args += (person_nick,)
                query += ",nick"

            query += ") VALUES (%s,%s"
            if person_nick:
                query += ",%s"
            query += ")"
            self.cursor.execute(query, args)

        reply = "Information stored for %s:%s:%s - " % (p.x, p.y, p.z)
        reply += "alliance=%s" % (alliance_name,)
        if person_nick:
            reply += " nick=%s" % (person_nick,)
        self.client.reply(prefix, nick, target, reply)

        # do stuff here

        return 1
