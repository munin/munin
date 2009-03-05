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

class mydef(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s*(\d)\s*x\s+(.*)")
        self.countre=re.compile(r"(\d+(?:.\d+)?[mk]?)")
        self.shipre=re.compile(r"(\w+),?")
        self.usage=self.__class__.__name__ + ""
	self.helptext=None

    def execute(self,user,access,irc_msg):
        m=self.commandre.search(irc_msg.command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        u=self.load_user(user,irc_msg)
        if not u:
            return
        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        fleetcount=m.group(1)
        garbage=m.group(2)
        # assign param variables

        (ships, comment) = self.parse_garbage(garbage)
        if self.reset_ships_and_comment(u,ships,fleetcount,comment):
            irc_msg.reply("Updated your def info to: fleetcount %s, comment: %s and ships: %s"%(fleetcount,comment,", ".join(map(lambda x:"%s %s" %(self.format_real_value(ships[x]),x),ships.keys()))))
        else:
            irc_msg.reply("Bork")
        
        return 1

    def reset_ships_and_comment(self,user,ships,fleetcount,comment):
        if not self.update_comment_and_fleetcount(user.pnick,fleetcount,comment):
            return False
        if not self.update_fleets(user,ships):
            return False
        return True
        
    def update_fleets(self,user,ships):
        query="DELETE FROM user_fleet WHERE user_id = %s"
        self.cursor.execute(query,(user.id,))

        for k in ships.keys():
            query="INSERT INTO user_fleet (user_id,ship,ship_count)"
            query+=" VALUES (%s,%s,%s)"
            args=(user.id,k,ships[k])
            self.cursor.execute(query,args)
        return True
    
    def update_comment_and_fleetcount(self,user,fleetcount,comment):
        query="UPDATE user_list SET fleetcount=%s, fleetcomment=%s WHERE pnick ilike %s"
        args=(fleetcount,comment,user)
        self.cursor.execute(query,args)
        if self.cursor.rowcount < 1:
            return False
        return True


    def parse_garbage(self,garbage):
        parts=garbage.split()
        print parts
        ships={}
        while len(parts) > 1:
            mc=self.countre.match(parts[0])
            ms=self.shipre.match(parts[1])
            if not mc or not ms:
                break

            count=self.human_readable_number_to_integer(mc.group(1))
            ship=ms.group(1)

            query="SELECT * FROM ship WHERE name ILIKE %s"

            self.cursor.execute(query,("%"+ship+"%",))
            s=self.cursor.dictfetchone()
            if s:
                ship=s['name']                
            elif ship.lower() not in ['fi','co','fr','de','cr','bs']:
                break

            ships[ship]=count
            
            
            parts.pop(0)
            parts.pop(0)
        comment=" ".join(parts)
        return (ships, comment)
