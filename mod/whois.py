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



class whois(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + ""
	self.helptext=None

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        
        # assign param variables 
        search=m.group(1)

        # do stuff here
        
        if search.lower() == 'munin':
            self.client.reply(prefix,nick,target,"I am Munin. Hear me roar.")
            return 1
        
        query="SELECT pnick,sponsor,invites"
        query+=" FROM user_list"
        query+=" WHERE pnick ilike %s"
        query+=" AND userlevel >= 100"

        self.cursor.execute(query,(search,))

        reply=""
        if self.cursor.rowcount < 1:
            self.cursor.execute(query,('%'+search+'%',))

        r=self.cursor.dictfetchone()

        if not r:
            reply+="No members matching '%s'"%(search,)
        else:
            if r['pnick'] == user:
                reply+="You are %s. Your sponsor is %s. You have %s invite%s left."
            else:
                reply+="Information about %s: Their sponsor is %s. They have %s invite%s left."
            reply=reply%(r['pnick'],r['sponsor'],r['invites'],['','s'][r['invites']!=1])

        self.client.reply(prefix,nick,target,reply)
        
        return 1
