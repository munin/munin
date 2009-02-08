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

class roidsave(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,1)
        self.paramre=re.compile(r"^\s+(\d+)\s+(\d+)",re.I)
        self.usage=self.__class__.__name__ + " <roids> <ticks>"
        self.helptext=['Tells you how much value will be mined by a number of roids in that many ticks. M=Max, F=Feudalism, D=Democracy.']
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
        mining=250

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
              
        cost=self.format_value(ticks*roids*mining)

        cost_m=self.format_value(int(ticks*roids*mining*1.9529))
        cost_f=self.format_value(int(ticks*roids*mining*(1/(1-float(self.config.get('Planetarion', 'feudalism'))))))
        cost_d=self.format_value(int(ticks*roids*mining*.9524))
        
        reply="%s roids will mine %s value (M: %s/F: %s/D: %s) in %s ticks (%s days)" % (roids,cost,cost_m,cost_f,cost_d,ticks,ticks/24)

        
        irc_msg.reply(reply)

        return 1
