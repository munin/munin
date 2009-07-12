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

import re
from munin import loadable

class remuser(loadable.loadable):
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,1000)
        self.paramre=re.compile(r"^\s+(\S+)")

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        u=self.load_user(user,irc_msg)
        if not u: return 0


        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: remuser <p-nick>")
            return 0
        
        pnick=m.group(1).lower()         
        
        query="SELECT id,pnick,userlevel FROM user_list WHERE pnick ILIKE %s LIMIT 1"
        self.cursor.execute(query,(pnick,))
        res=self.cursor.dictfetchone()
        if not res:
            irc_msg.reply("User '%s' does not exist" % (pnick,))
            return 0
        access_lvl = res['userlevel']
        real_pnick = res['pnick']
        uid = res['id']
        
        if access_lvl >= access:
            irc_msg.reply("You may not remove %s, his or her access (%s) exceeds your own (%s)" % (pnick, access_lvl, access))
            return 0

        query="DELETE FROM target WHERE uid=%s"
        self.cursor.execute(query,(uid,))
        
        query="DELETE FROM user_list WHERE pnick=%s"
        
        try:
            self.cursor.execute(query,(real_pnick,))
            if self.cursor.rowcount>0:
                irc_msg.client.privmsg('p','remuser #%s %s'%(self.config.get('Auth', 'home'), real_pnick,))
                irc_msg.client.privmsg('p',"ban #%s *!*@%s.users.netgamers.org "%(self.config.get('Auth', 'home'), real_pnick,))
                irc_msg.reply("Removed user %s" % (real_pnick,))
            else:
                irc_msg.reply("No user removed" )
        except:
            raise
        return 1
            
            
