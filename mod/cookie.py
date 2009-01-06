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



class cookie(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+((\d+)\s+)?(\S+)\s+(\S.+)")
        self.usage=self.__class__.__name__ + " [howmany] <receiver> <reason>"
	self.helptext=["Cookies are used to give out carebears. Carebears are rewards for carefaces. Give cookies to people when you think they've done something benificial for you or for the alliance in general."]

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        u=self.load_user(user,prefix,nick,target)
        if not u: return 0


        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        if target.lower() != "#"+self.config.get("Auth","home").lower():
            self.client.reply(prefix,nick,target,"This command may only be used in #%s."%(self.config.get("Auth","home"),))
            return 1
        # assign param variables 
        howmany=m.group(2)
        if howmany:
            howmany=int(howmany)
        else:
            howmany=1
        receiver=m.group(3)
        reason=m.group(4)

        if not self.can_give_cookies(prefix,nick,target,u,howmany):
            return 0

        #rec=load_user
        rec=self.load_user_from_pnick(receiver)
        if not rec or rec.userlevel < 100:
            self.client.reply(prefix,nick,target,"I don't know who '%s' is, so I can't very well give them any cookies can I?" % (receiver,))
            return 1
        if u.pnick == rec.pnick:
            self.client.reply(prefix,nick,target,"Fuck you, %s. You can't have your cookies and eat them, you selfish dicksuck."%(u.pnick,))
            return 1

        query="UPDATE user_list SET carebears = carebears + %d WHERE id = %s"
        self.cursor.execute(query,(howmany,rec.id))
        query="UPDATE user_list SET available_cookies = available_cookies - %d WHERE id = %s"
        self.cursor.execute(query,(howmany,u.id))
        self.client.reply(prefix,nick,target,
                          "%s said '%s' and gave %d %s to %s, who stuffed their face and now has %d carebears"%(u.pnick,
                                                                                                                reason,
                                                                                                                howmany,
                                                                                                                self.pluralize(howmany,"cookie"),
                                                                                                                rec.pnick,
                                                                                                                rec.carebears+howmany))
        #self.client.reply(prefix, nick, target, "'%s' - '%s' - '%s' " % (howmany,receiver,reason))

        # do stuff here

        return 1

    def can_give_cookies(self,prefix,nick,target,u,howmany):
        available_cookies = u.check_available_cookies(self.conn,self.client,self.cursor,self.config)
        if howmany > available_cookies:
            reply="Silly, %s. You currently only have %s cookies to give out, but are trying to give out %s cookies. I'll bake you some new cookies on Monday morning." % (u.pnick, u.available_cookies, howmany)
            self.client.reply(prefix, nick, target, reply)
            return False
        return True
