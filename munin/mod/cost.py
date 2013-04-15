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

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08

import re
from munin import loadable

class cost(loadable.loadable):
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,1)
        self.paramre=re.compile(r"^\s+(\d+(?:\.\d+)?[mk]?)\s+(\S+)(?:\s+(\S+))?")
        self.usage=self.__class__.__name__ + " <number> <shipname> [government]"

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        ship_number=m.group(1)

        if ship_number[-1].lower()=='k':
            ship_number=1000*float(ship_number[:-1])
        elif ship_number[-1].lower()=='m':
            ship_number=1000000*float(ship_number[:-1])
        else:
            ship_number=float(ship_number)
        ship_number=int(ship_number)
        ship_name=m.group(2)

        gov_name=m.group(3).lower()
        prod_bonus=1
        if gov_name in "totalitarianism":
            prod_bonus=1-float(self.config.get('Planetarion', 'totalitarianism'))
            gov_name="Totalitarianism"
        elif gov_name in "democracy":
            prod_bonus=1-float(self.config.get('Planetarion', 'democracy'))
            gov_name="Democracy"

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        ship=self.get_ship_from_db(ship_name)
        if not ship:
            irc_msg.reply("%s is not a ship" % (ship_name))
            return 0

        metal=int(ship['metal']     * prod_bonus) * ship_number
        crystal=int(ship['crystal'] * prod_bonus) * ship_number
        eonium=int(ship['eonium']   * prod_bonus) * ship_number
        resource_value=(metal+crystal+eonium)/150
        ship_value=(ship['total_cost'] * ship_number)/100
        reply="Buying %s %s will cost %s metal, %s crystal and %s eonium"%(
            ship_number, ship['name'], metal, crystal, eonium)

        if prod_bonus != 1:
            reply+=" as %s"%(gov_name)

        reply+=". This gives %s ship value (%s increase)"%(
            ship_value, ship_value - resource_value)

        irc_msg.reply(reply)

        return 1
