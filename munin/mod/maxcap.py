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

# No alliance specific things found in this module.
# qebab, 24/6/08.

import re
from munin import loadable


class maxcap(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(\d+)(?:[-.:\s](\d+)[-.:\s](\d+)(?:\s+(\d+)[-.:\s](\d+)[-.:\s](\d+))?)?")
        self.usage = self.__class__.__name__ + " <defender coords> [attacker coords]"
        self.helptext = [
            "Show how many roids you will cap from a target. If you have your"
            " planet set, your actual cap rate will be used, otherwise max cap"
            " is assumed. You can also manually specify attacker coords."
        ]

    def execute(self, user, access, irc_msg):
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        victim = None
        attacker = None
        m = self.paramre.search(irc_msg.command_parameters)
        if m:
            if m.lastindex == 1:
                total_roids = int(m.group(1))
            else:
                victim = loadable.planet(x=m.group(1), y=m.group(2), z=m.group(3))
                if not victim.load_most_recent(self.cursor, irc_msg.round):
                    irc_msg.reply(
                        "%s:%s:%s is not a valid planet" % (victim.x, victim.y, victim.z)
                    )
                    return 1
                total_roids = victim.size
                if m.lastindex >= 6:
                    attacker = loadable.planet(x=m.group(4), y=m.group(5), z=m.group(6))
                    attacker = loadable.planet(x=m.group(4), y=m.group(5), z=m.group(6))
                    if not attacker.load_most_recent(self.cursor, irc_msg.round):
                        irc_msg.reply(
                            "%s:%s:%s is not a valid planet"
                            % (attacker.x, attacker.y, attacker.z)
                        )
                        return 1
                else:
                    user = self.load_user_from_pnick(user, irc_msg.round)
                    if user.planet:
                        attacker = user.planet
        else:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        cap = 0
        cap_rate = 0.25
        if attacker and victim:
            cap_rate = attacker.cap_rate(victim)

        reply = ""
        for i in range(1, 5):
            cap += int(total_roids * cap_rate)
            reply += "Wave %d: %d (%d), " % (i, int(total_roids * cap_rate), cap)
            total_roids = total_roids - int(total_roids * cap_rate)
        irc_msg.reply("Caprate: %s%% %s" % (int(cap_rate * 100), reply.strip(", ")))

        return 1
