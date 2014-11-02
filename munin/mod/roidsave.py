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

# Nothing alliance specific here.
# qebab, 24/6/08.

import re
from munin import loadable

class roidsave(loadable.loadable):
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,1)
        self.paramre=re.compile(r"^\s+(\d+)\s+(\d+)(\s+(\d+))?",re.I)
        self.usage=self.__class__.__name__ + " <roids> <ticks> [mining_bonus]"
        self.helptext=['Tells you how much value will be mined by a number of roids in that many ticks.']
    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        roids=int(m.group(1))
        ticks=int(m.group(2))
        bonus=m.group(4) or 0
        bonus=int(bonus)
        mining=250

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        mining = int(mining *(float(bonus+100)/100))

        cost=self.format_value(ticks*roids*mining)
        cost_demo=self.format_value(int(ticks*roids*mining*(1/(1-float(self.config.get('Planetarion', 'democracy_cost_reduction'))))))
        cost_tota=self.format_value(int(ticks*roids*mining*(1/(1-float(self.config.get('Planetarion', 'totalitarianism_cost_reduction'))))))

        reply="%s roids with %s%% bonus will mine %s value (Democracy: %s, Totalitarianism: %s) in %s ticks (%s days)" % (roids,bonus,cost,cost_demo,cost_tota,ticks,ticks/24)

        irc_msg.reply(reply)

        return 1
