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

# Nothing ascendancy specific in this module.
# qebab, 24/6/08.

class stop(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,1)
        self.paramre=re.compile(r"^\s+(\d+[mk]?)\s+(\S+)(\s+(t1|t2|t3))?")
        self.usage=self.__class__.__name__ + " <number> <ship to stop>"

    def execute(self,nick,target,prefix,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0
        params=m.group(1)
        m=self.paramre.search(params)
        if not m:
            if re.search("\s+hammertime",params,re.I):
                irc_msg.reply("Can't touch this!")
                return 1
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        ship_number=m.group(1)
        
        if ship_number[-1].lower()=='k':
            ship_number=1000*int(ship_number[:-1])
        elif ship_number[-1].lower()=='m':
            ship_number=1000000*int(ship_number[:-1])
        else:
            ship_number=int(ship_number)        

        bogey=m.group(2)        
        
        user_target=m.group(4)
        efficiency = 1.0
        
        target_number=None
        if not user_target or user_target == "t1":
            target_number="target_1"
            user_target="t1"
        elif user_target == "t2":
            target_number="target_2"
            efficiency = .6
        elif user_target == "t3":
            target_number="target_3"
            efficiency = .3
            
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        query="SELECT * FROM ship WHERE name ILIKE %s ORDER BY id"
                
        self.cursor.execute(query,("%"+bogey+"%",))
        ship=self.cursor.dictfetchone()
        if not ship:
            if "asteroids".rfind(bogey) > -1:
                ship={'name':'Asteroid','class':'Roids','armor':50,'total_cost':20000}
            elif "structures".rfind(bogey) > -1:
                ship={'name':'Structure','class':'Struct','armor':500,'total_cost':150000}
            else:
                irc_msg.reply("%s is not a ship" % (bogey))
                return 0
        total_armor=ship['armor']*ship_number

        # do stuff here
        query="SELECT * FROM ship WHERE "+target_number+"=%s ORDER BY id"
        self.cursor.execute(query,(ship['class'],))
        attackers=self.cursor.dictfetchall()
        
        reply=""
        
        if len(attackers)==0:
            reply="%s is not hit by anything as category %s" % (ship['name'],user_target)
        else:
            if ship['class'].lower() == "roids":
                reply+="Capturing "
            elif ship['class'].lower() == "struct":
                reply+="Destroying "
            else:
                reply+="Stopping "
            reply+="%s %s (%s) as %s requires " % (ship_number,ship['name'],self.format_value(ship_number*ship['total_cost']),user_target)
    
            for a in attackers:
                if a['type'] == "Emp" :
                    needed=int((math.ceil(ship_number/(float(100-ship['empres'])/100)/a['gun']))/efficiency)
                else:
                    needed=int((math.ceil(float(total_armor)/a['damage']))/efficiency)
                reply+="%s: %s (%s) " % (a['name'],needed,self.format_value(a['total_cost']*needed))
        
            
        irc_msg.reply(reply.strip())
            
        return 1

