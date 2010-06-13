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

class logdef(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,100)
        self.paramre=re.compile(r"^\s*(.*)")
        self.ship_classes = ['fi','co','fr','de','cr','bs']
        self.usage=self.__class__.__name__ + ""
	self.helptext=None

    def execute(self,user,access,irc_msg):
        m=self.commandre.search(irc_msg.command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        search=m.group(1)
        hit={}

        hit=self.search_by_ship(irc_msg,search)

        u=self.load_user_from_pnick(search)
        if not hit and u:
            hit=self.search_by_user(irc_msg,u)

        if hit:
            cur=self.current_tick()
            reply=", ".join(map(lambda x:"%s gave %s %s to %s (%s)"%(x['owner'],self.format_real_value(x['ship_count']),
                                                                     x['ship'],x['taker'],x['tick']-cur),hit))
            irc_msg.reply(reply)
        else:
            irc_msg.reply("No matches found in the deflog for search '%s'"%(search,))
    
        return 1


    def search_by_user(self,irc_msg,user):
        query=self.base_query()
        query+=" WHERE t3.id=%s"
        query+=" ORDER BY t1.tick DESC"
        query+=" LIMIT 5"
        
        self.cursor.execute(query,(user.id,))

        if self.cursor.rowcount > 0:
            return self.cursor.dictfetchall()
        return False

    def search_by_ship(self,irc_msg,ship):
        lookup=ship
        if ship not in self.ship_classes:
            lookup='%' + ship + '%'
        query=self.base_query()
        query+=" WHERE t1.ship ilike %s"
        query+=" ORDER BY t1.tick DESC"
        query+=" LIMIT 5"

        self.cursor.execute(query,(lookup,))

        if self.cursor.rowcount > 0:
            return self.cursor.dictfetchall()

        return False

    def base_query(self):
        query="SELECT t2.pnick AS taker,t3.pnick AS owner,t1.ship,t1.ship_count,t1.tick"
        query+=" FROM fleet_log AS t1"
        query+=" INNER JOIN user_list AS t2"
        query+=" ON t2.id=t1.taker_id"
        query+=" INNER JOIN user_list AS t3"
        query+=" ON t3.id=t1.user_id"
        return query
