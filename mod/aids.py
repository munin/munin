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



class aids(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + ""
	self.helptext=None

    def execute(self,nick,username,host,target,prefix,command,user,access,irc_msg):
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
            # Hardcoded == bad?
            self.client.reply(prefix,nick,target,"I am Munin. I gave aids to all you bitches.")
            return 1
        
        u=loadable.user(pnick=search)
        if not u.load_from_db(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"No users matching '%s'"%(search,))
            return 1
        if u.userlevel < 100:
            self.client.reply(prefix,nick,target,"%s is not a member, his aids is worthless."%(u.pnick,))
            return 1

        query="SELECT pnick,sponsor,invites"
        query+=" FROM user_list"
        query+=" WHERE sponsor ilike %s"
        query+=" AND userlevel >= 100"

        self.cursor.execute(query,(u.pnick,))

        reply=""


        if u.pnick == user:
            reply+="You are %s." % (u.pnick,)
            if self.cursor.rowcount < 1:
                reply+=" You have greedily kept your aids all to yourself."
            else:
                reply+=" You have given aids to: "
                prev=[]
                for r in self.cursor.dictfetchall():
                    prev.append(r['pnick'])
                reply+=", ".join(prev)
        else:
            if self.cursor.rowcount < 1:
                reply+="%s hasn't given anyone aids, what a selfish prick" %(u.pnick,)
            else:
                reply+="%s has given aids to: " % (u.pnick,)
                prev=[]
                for r in self.cursor.dictfetchall():
                    prev.append(r['pnick'])
                reply+=", ".join(prev)


        self.client.reply(prefix,nick,target,reply)
        
        return 1
