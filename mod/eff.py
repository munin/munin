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

# This module doesn't have anything alliance specific as far as I can tell.
# qebab, 24/6/08.

class eff(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,1)
        self.paramre=re.compile(r"^\s+(\d+(?:.\d+)?[mk]?)\s+(\S+)(\s+(t1|t2|t3))?")
        self.usage=self.__class__.__name__ + " <number> <shipname> [t1|t2|t3]"

    def execute(self,nick,target,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        ship_number=m.group(1)
        ship_name=m.group(2)
        user_target=m.group(4)
        efficiency = 1.0
        target_number=None
        if not user_target or user_target == "t1":
            target_number = "target_1"
            user_target = "t1"
        elif user_target == "t2":
            target_number = "target_2"
            efficiency = .6
        elif user_target == "t3":
            target_number = "target_3"
            efficiency = .3
        # assign param variables
        if ship_number[-1].lower()=='k':
            ship_number=1000*float(ship_number[:-1])
        elif ship_number[-1].lower()=='m':
            ship_number=1000000*float(ship_number[:-1])
        else:
            ship_number=float(ship_number)        
        ship_number=int(ship_number)

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        query="SELECT * FROM ship WHERE name ILIKE %s ORDER BY id"
        
        self.cursor.execute(query,("%"+ship_name+"%",))
        ship=self.cursor.dictfetchone()
        if not ship:
            irc_msg.reply("%s is not a ship" % (ship_name))
            return 0
        if ship['damage']:
            total_damage=ship['damage']*ship_number
        
        if ship['target_1'] == 'Roids':
            killed=total_damage/50
            irc_msg.reply("%s %s (%s) will capture Asteroid: %s (%s)" % (ship_number,ship['name'],self.format_value(ship_number*ship['total_cost']),killed,self.format_value(killed*20000)))
        elif ship['target_1'] == 'Struct':
            killed=total_damage/500
            irc_msg.reply("%s %s (%s) will destroy Structure: %s (%s)" % (ship_number,ship['name'],self.format_value(ship_number*ship['total_cost']),killed,self.format_value(killed*150000)))
            pass
        else:
            query="SELECT * FROM ship WHERE class=%s ORDER BY id"
            self.cursor.execute(query,(ship[target_number],))
            targets=self.cursor.dictfetchall()
            if len(targets) == 0:
                reply="%s does not have any targets in that category (%s)" % (ship['name'],user_target)
            else:
                reply="%s %s (%s) hitting %s will " % (ship_number,ship['name'],self.format_value(ship_number*ship['total_cost']),user_target)
                if ship['type'].lower() == "norm" or ship['type'].lower() == 'cloak':
                    reply+="destroy "
                elif ship['type'].lower() == "emp":
                    reply+="freeze "
                elif ship['type'].lower() == "steal":
                    reply+="steal "
                else:
                    raise Exception("Erroneous type %s" % (ship['type'],))
                for t in targets:
                    if ship['type'].lower() == "emp" :
                        killed=int(efficiency * ship['gun']*ship_number*float(100-t['empres'])/100)
                    else:
                        killed=int(efficiency * total_damage/t['armor'])
                    reply+="%s: %s (%s) " % (t['name'],killed,self.format_value(t['total_cost']*killed))
            irc_msg.reply(reply.strip())
                                
                
        return 1
