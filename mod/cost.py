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

class cost(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,1)
        self.paramre=re.compile(r"^\s+(\d+(?:.\d+)?[mk]?)\s+(\S+)")
        self.usage=self.__class__.__name__ + " <number> <shipname>"

    def execute(self,nick,target,command,user,access,irc_msg):
        m=self.commandre.search(command)
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
                
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        query="SELECT * FROM ship WHERE name ILIKE %s"

        self.cursor.execute(query,("%"+ship_name+"%",))
        ship=self.cursor.dictfetchone()
        if not ship:
            irc_msg.reply("%s is not a ship" % (ship_name))
            return 0

        feudalism = 1-float(self.config.get('Planetarion', 'feudalism'))

        reply="Buying %s %s will cost %s metal, %s crystal and %s eonium."%(ship_number,ship['name'],ship['metal'] * ship_number,
                                                                            ship['crystal'] * ship_number,ship['eonium'] * ship_number)

        reply+=" Feudalism: %s metal, %s crystal and %s eonium."%(int(ship['metal'] * feudalism) * ship_number,int(ship['crystal'] * feudalism)* ship_number,
                                                                  int(ship['eonium'] * feudalism) * ship_number)
        
#        reply+=" Dictatorship: %s metal, %s crystal and %s eonium."%(int(ship['metal'] * 1.05)*ship_number,int(ship['crystal'] *1.05) *ship_number,
#                                                                  int(ship['eonium'] * 1.05)*ship_number)

        reply+=" It will add %s value"%((ship['total_cost'] * ship_number)/100,)
        

        irc_msg.reply(reply)
        
        return 1
        
"""        
        if not ship:
            if "asteroids".rfind(bogey) > -1:
                irc_msg.reply("Buying %s %s will cost %s metal, %s crystal and %s eonium. It will add %s value" %(ship_number,ship['name'],
                                                                                                                                         ship['metal'] * ship_number,
                                                                                                                                         ship['crystal'] * ship_number,
                                                                                                                                         ship['eonium'] * ship_number,
                                                                                                                                         (ship['total_cost'] * ship_number)/100))
                
                ship={'name':'Asteroid','class':'Roids','armor':50,'total_cost':20000}
            elif "structures".rfind(bogey) > -1:
                
                ship={'name':'Structure','class':'Struct','armor':500,'total_cost':150000}
            else:
                irc_msg.reply("%s is not a ship" % (bogey))
                return 0
"""                
