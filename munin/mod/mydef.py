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
        super(self.__class__,self).__init__(cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s*(\d)\s*x\s*(.*)")
        self.countre=re.compile(r"^(\d+(?:\.\d+)?[mk]?)$")
        self.shipre=re.compile(r"^(\w+),?$")
        self.nulls = ["<>",".","-","?"]
        self.ship_classes = ['fi','co','fr','de','cr','bs']
        self.usage=self.__class__.__name__ + " [fleets] x <[ship count] [ship name]> [comment]"
	self.helptext=["Add your fleets for defense listing. Ship can be a shipclass. For example !"+self.__class__.__name__+" 2x 20k Barghest 30k Harpy 20k BS Call me any time for hot shipsex."]

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
        reset_ships=False
        ships={}
        comment=""
        if garbage in self.nulls:
            reset_ships=True
        else:
            (ships, comment)=self.parse_garbage(garbage)

        (ships,comment)=self.reset_ships_and_comment(u,ships,fleetcount,comment,reset_ships)

        irc_msg.reply("Updated your def info to: fleetcount %s, updated: pt%s ships: %s and comment: %s"%(fleetcount,self.current_tick(),", ".join(map(lambda x:"%s %s" %(self.format_real_value(x['ship_count']),x['ship']),ships)),comment))

        return 1

    def reset_ships_and_comment(self,user,ships,fleetcount,comment,reset_ships):
        comment=self.update_comment_and_fleetcount(user,fleetcount,comment)
        if len(ships) > 0 or reset_ships:
            self.update_fleets(user,ships)
        ships=user.get_fleets(self.cursor)
        return (ships,comment)
        
    def update_fleets(self,user,ships):
        query="DELETE FROM user_fleet WHERE user_id = %s"
        self.cursor.execute(query,(user.id,))

        for k in ships.keys():
            query="INSERT INTO user_fleet (user_id,ship,ship_count)"
            query+=" VALUES (%s,%s,%s)"
            args=(user.id,k,ships[k])
            self.cursor.execute(query,args)
    
    def update_comment_and_fleetcount(self,user,fleetcount,comment):
        query="UPDATE user_list SET fleetcount=%s"
        args=(fleetcount,)
        if comment != "":
            if comment in self.nulls:
                comment=""
            args+=(comment,)
            query+=", fleetcomment=%s"
        query+=",fleetupdated=%s"
        args+=(self.current_tick(),)
        query+=" WHERE id = %s"
        args+=(user.id,)
        self.cursor.execute(query,args)
        query="SELECT fleetcomment FROM user_list WHERE id = %s"
        self.cursor.execute(query,(user.id,))
        return self.cursor.dictfetchone()['fleetcomment']

    def parse_garbage(self,garbage):
        parts=garbage.split()
        ships={}
        while len(parts) > 1:
            mc=self.countre.match(parts[0])
            ms=self.shipre.match(parts[1])
            if not mc or not ms:
                break

            count=self.human_readable_number_to_integer(mc.group(1))
            ship=ms.group(1)

            ship=self.get_ship_from_db(ship_name)

            if ship.lower() not in self.ship_classes and s:
                ship=s['name']                
            elif ship.lower() not in self.ship_classes:
                break

            ships[ship]=count
            
            
            parts.pop(0)
            parts.pop(0)
        comment=" ".join(parts)
        return (ships, comment)
