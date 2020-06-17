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


class spamin(loadable.loadable):
    """
    Set a bunch of planets as belonging to the given alliance.
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(.*?)\s([0-9:. ]+)")
        self.usage = self.__class__.__name__ + " <alliance> <coords...>"
        self.helptext = None

        self.coordsplitre = re.compile(r"[:. ]")

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        alliance_name = m.group(1)
        coord_list = re.split(self.coordsplitre, m.group(2))

        if len(coord_list) % 3 != 0:
            irc_msg.reply("You did not give me a set of complete coords, you dumbass!")
            return 0

        # do stuff here
        a = loadable.alliance(name=alliance_name)
        if not a.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply("No alliance matching ' %s' found" % (alliance_name))
            return 0

        # Separate X from Y from Z coords.
        xs = coord_list[0::3]
        ys = coord_list[1::3]
        zs = coord_list[2::3]

        # Get planet IDs for the given coords.
        pids = ()
        coords = ()
        skipped = ()
        for i in range(0, len(xs)):
            p = loadable.planet(x=xs[i], y=ys[i], z=zs[i])
            if p.load_most_recent(self.cursor, irc_msg.round):
                pids += (p.id,)
                coords += ("%s:%s:%s" % (p.x, p.y, p.z),)
            else:
                skipped += ("%s:%s:%s" % (p.x, p.y, p.z),)

        if len(skipped) > 0:
            irc_msg.reply(
                "The following coords do not exist, try again: %s"
                % (", ".join(skipped))
            )
            return 0

        # Interleave alliance ID with the current round number and planet IDs:
        # pid1, aid, round, pid2, aid, round, etc.
        aids = (a.id,) * len(pids)
        rounds = (irc_msg.round,) * len(pids)
        values = tuple(val for pair in zip(pids, aids, rounds) for val in pair)

        # Make a query with 'len(pids)' value lists.
        query = "INSERT INTO intel (pid, alliance_id, round) VALUES %s" % (
            " , ".join(("(%s, %s, %s)",) * len(pids))
        )
        query += " ON CONFLICT (pid) DO"
        query += " UPDATE SET alliance_id = EXCLUDED.alliance_id"
        self.cursor.execute(query, values)
        if self.cursor.rowcount < 1:
            irc_msg.reply("Failed to change intel, go whine to the bot owner.")
            return 0

        irc_msg.reply("Set alliance for %s to %s" % (", ".join(coords), a.name,))
        return 1
