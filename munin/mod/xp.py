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

# Nothing hardcoded found here.
# qebab, 24/6/08.

import re
from munin import loadable


class xp(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(
            r"^\s*(\d+)[.-:\s](\d+)[.-:\s](\d+)(?:\s+(\d+)[.-:\s](\d+)[.-:\s](\d+))?(?:\s+(\d+))?"
        )
        self.usage = (
            self.__class__.__name__ + " <defender coords> [attacker coords] [MCs]"
        )

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        victim = None
        attacker = None
        mcs = 0

        victim = loadable.planet(x=m.group(1), y=m.group(2), z=m.group(3))
        if not victim.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply(
                "%s:%s:%s is not a valid planet" % (victim.x, victim.y, victim.z)
            )
            return 1

        if not victim:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 1

        if m.lastindex >= 6 and m.group(4) and m.group(5) and m.group(6):
            attacker = loadable.planet(x=m.group(4), y=m.group(5), z=m.group(6))
            if not attacker.load_most_recent(self.cursor, irc_msg.round):
                irc_msg.reply(
                    "%s:%s:%s is not a valid planet"
                    % (attacker.x, attacker.y, attacker.z)
                )
                return 1
        if not attacker:
            u = loadable.user(pnick=irc_msg.user)
            u.load_from_db(self.cursor, irc_msg.round)
            if not u.planet:
                irc_msg.reply(
                    "You must be registered to use the automatic %s command (log in with P and "
                    "set mode +x, then make sure your planet is set with the pref command (!pref planet=x:y:z))"
                    % (self.__class__.__name__)
                )
                return 1
            attacker = u.planet

        if m.lastindex == 7:
            mcs = int(m.group(7))

        reply = "Target %s:%s:%s (%s|%s) " % (
            victim.x,
            victim.y,
            victim.z,
            self.format_real_value(victim.value),
            self.format_real_value(victim.score),
        )
        reply += "| Attacker %s:%s:%s (%s|%s) " % (
            attacker.x,
            attacker.y,
            attacker.z,
            self.format_real_value(attacker.value),
            self.format_real_value(attacker.score),
        )

        bravery = attacker.bravery(victim)
        cap = int(attacker.cap_rate(victim) * victim.size)
        xp = int(attacker.calc_xp(victim, mcs))
        score = self.format_real_value(60 * xp)

        reply += "| Bravery: %.2f | Cap: %d | MCs: %d | XP: %d | Score: %s" % (
            bravery,
            cap,
            mcs,
            xp,
            score,
        )
        irc_msg.reply(reply)
        return 1
