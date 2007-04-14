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

class remuser(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,500)
        self.paramre=re.compile(r"^\s+(\S+)")

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: remuser <p-nick>")
            return 0
        
        pnick=m.group(1).lower()         
        
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to remove users")
            return 0
        
        
        query="SELECT id,pnick,userlevel FROM user_list WHERE pnick ILIKE %s LIMIT 1"
        self.cursor.execute(query,(pnick,))
        res=self.cursor.dictfetchone()
        if not res:
            self.client.reply(prefix,nick,target,"User '%s' does not exist" % (pnick,))
            return 0
        access_lvl = res['userlevel']
        real_pnick = res['pnick']
        uid = res['id']
        
        if access_lvl >= access:
            self.client.reply(prefix,nick,target,"You may not remove %s, his or her access (%s) exceeds your own (%s)" % (pnick, access_lvl, access))
            return 0

        query="DELETE FROM target WHERE uid=%s"
        self.cursor.execute(query,(uid,))
        
        query="DELETE FROM user_list WHERE pnick=%s"
        
        try:
            self.cursor.execute(query,(real_pnick,))
            if self.cursor.rowcount>0:
                self.client.reply(prefix,nick,target,"Removed user %s" % (real_pnick,))
            else:
                self.client.reply(prefix,nick,target,"No user removed" )
        except:
            raise
        return 1
            
            
