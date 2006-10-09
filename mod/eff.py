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

class eff(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^\s+(\d+[mk]?)\s+(\S+)")
        self.usage=self.__class__.__name__ + " <number> <shipname>"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        ship_number=m.group(1)
        ship_name=m.group(2)
        # assign param variables
        if ship_number[-1].lower()=='k':
            ship_number=1000*int(ship_number[:-1])
        elif ship_number[-1].lower()=='m':
            ship_number=1000000*int(ship_number[:-1])
        else:
            ship_number=int(ship_number)        

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        query="SELECT * FROM ship WHERE name ILIKE %s"
        
        self.cursor.execute(query,("%"+ship_name+"%",))
        ship=self.cursor.dictfetchone()
        if not ship:
            self.client.reply(prefix,nick,target,"%s is not a ship" % (ship_name))
            return 0
        total_damage=ship['damage']*ship_number
        
        if ship['target'] == 'Roids':
            killed=total_damage/50
            self.client.reply(prefix,nick,target,"%s %s (%s) will capture Asteroid: %s (%s)" % (ship_number,ship['name'],self.format_value(ship_number*ship['total_cost']),killed,self.format_value(killed*20000)))
        elif ship['target'] == 'Struct':
            killed=total_damage/500
            self.client.reply(prefix,nick,target,"%s %s (%s) will destroy Structure: %s (%s)" % (ship_number,ship['name'],self.format_value(ship_number*ship['total_cost']),killed,self.format_value(killed*150000)))
            pass
        else:
            query="SELECT * FROM ship WHERE class=%s"
            self.cursor.execute(query,(ship['target'],))
            targets=self.cursor.dictfetchall()
            reply="%s %s (%s) will " % (ship_number,ship['name'],self.format_value(ship_number*ship['total_cost']))
            if ship['type'].lower() == "norm":
                reply+="destroy "
            elif ship['type'].lower() == "emp":
                reply+="freeze "
            elif ship['type'].lower() == "steal":
                reply+="steal "
            else:
                raise Exception("Erroneous type %s" % (ship['type'],))

            for t in targets:
                if ship['type'] == "Emp" :
                    killed=int(ship['gun']*ship_number*float(100-t['empres'])/100)
                else:
                    killed=total_damage/t['armor']
                reply+="%s: %s (%s) " % (t['name'],killed,self.format_value(t['total_cost']*killed))
            self.client.reply(prefix,nick,target,reply.strip())
                                
                
        return 1
