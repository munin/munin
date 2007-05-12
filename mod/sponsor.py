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

class sponsor(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)(\s+(.*))")
        self.usage=self.__class__.__name__ + " <pnick> <comments>"
        self.helptext=["This command is used to sponsor a new recruit. When you sponsor someone, you suggest them for recuitment to the alliance and state that you will make sure they're at home and don't fuck up. Once you've sponsored someone, make sure you speak to others about your possible invite, it is your responsibility to guarantee that they will be welcome.",
                   "After a set time period (currently 36 hours) you may use the !invite command to add them to the channel and Munin. You may at any point withdraw your sponsorship by using the unsponsor command. You may view currently pending sponsorships with !gimp. If you have any questions, good luck finding useful answers. "]
        
    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 1
        if not user:
            self.client.reply(prefix,nick,target,"You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
            return 1
        
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 1
        
        # assign param variables
        recruit=m.group(1)
        comment=m.group(3)
        
        # do stuff here
        if recruit.lower() == 'kila'.lower():
            reply="You have successfully invited '%s'. The gimp is now your responsibility. If they fuck up and didn't know, it's your fault. So teach them well." % (recruit,)
            self.client.reply(prefix,nick,target,reply)
            return 1
        query="SELECT * FROM sponsor(%s,%s,%s)"# AS t1(success BOOLEAN, retmessage TEXT)"
        self.cursor.execute(query,(user,recruit,comment))

        res=self.cursor.dictfetchone()
 
        if res['success']:
            reply="You have sponsored '%s' (MAKE SURE THIS IS THE RECRUIT'S PNICK.) In 36 hours you may use the !invite command to make them a member. It is your responsibility to get feedback about their suitability as a member in this period" % (recruit,)
        else:
            reply="You may not sponsor '%s'. Reason: %s"%(recruit,res['retmessage'])
        self.client.reply(prefix,nick,target,reply)        
        return 1
