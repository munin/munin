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



class unkick(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + " <pnick>"
	self.helptext=['This command is used to undo a vote for someone to be kicked out of the alliance. Your vote is removed and you instantly become a saint.']

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
        voter=loadable.user(pnick=user)
        if not voter.load_from_db(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
            return 1


        idiot=loadable.user(pnick=m.group(1))
        if not idiot.load_from_db(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"That idiot doesn't exist, if anyone wants to fix you being an idiot they can kickvote %s" % (voter.pnick,))
            return 1

        # do stuff here
        query="SELECT * FROM unkickvote(%s,%s)"

        self.cursor.execute(query,(voter.id,idiot.id))
        
        res=self.cursor.fetchone()

        if res['success']:
            reply="You have unkickvoted '%s', who now has %s of 7 votes necessary to kick" % (idiot.pnick,res['retmessage'])
        else:
            reply="You may not unkickvote '%s'. Reason: %s"%(idiot.pnick,res['retmessage'])

        self.client.reply(prefix,nick,target,reply)

        return 1
