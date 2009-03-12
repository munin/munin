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
from munin import loadable

class cookie(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.altparamre=re.compile(r"^\s+(\S+)\s+((\d+)\s+)?(\S.+)")
        self.paramre=re.compile(r"^\s+((\d+)\s+)?(\S+)\s+(\S.+)")
        self.statre=re.compile(r"^\s+statu?s?")
        self.usage=self.__class__.__name__ + " [howmany] <receiver> <reason> | [stat]"
	self.helptext=["Cookies are used to give out carebears. Carebears are rewards for carefaces. Give cookies to people when you think they've done something beneficial for you or for the alliance in general."]

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        u=self.load_user(user,irc_msg)
        if not u: return 0

        s=self.statre.search(m.group(1))
        m1=self.altparamre.search(m.group(1))
        m2=self.paramre.search(m.group(1))

        if not (m1 or m2 or s):
            print s
            print m2
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        if s:
            u=self.load_user(user,irc_msg)
            if not u: return 0
            self.show_status(irc_msg,u)
            return 1
        if self.command_not_used_in_home(irc_msg,self.__class__.__name__):
            return 1
        if m1:
            receiver=m1.group(2)            
            howmany=m1.group(3)
            reason=m1.group(4)
        else:
            howmany=m2.group(2)
            receiver=m2.group(3)
            reason=m2.group(4)
        if howmany:
            howmany=int(howmany)
        else:
            howmany=1
        

        if not self.can_give_cookies(irc_msg,u,howmany):
            return 0

        #rec=load_user

        if receiver.lower() == self.config.get('Connection','nick').lower():
            irc_msg.reply("Cookies? Pah! I only eat carrion.")
            return 1

        rec=self.load_user_from_pnick(receiver)
        if not rec or rec.userlevel < 100:
            irc_msg.reply("I don't know who '%s' is, so I can't very well give them any cookies can I?" % (receiver,))
            return 1
        if u.pnick == rec.pnick:
            irc_msg.reply("Fuck you, %s. You can't have your cookies and eat them, you selfish dicksuck."%(u.pnick,))
            return 1

        query="UPDATE user_list SET carebears = carebears + %d WHERE id = %s"
        self.cursor.execute(query,(howmany,rec.id))
        query="UPDATE user_list SET available_cookies = available_cookies - %d WHERE id = %s"
        self.cursor.execute(query,(howmany,u.id))
        irc_msg.reply("%s said '%s' and gave %d %s to %s, who stuffed their face and now has %d carebears"%(u.pnick,
                                                                                                            reason,
                                                                                                            howmany,
                                                                                                            self.pluralize(howmany,"cookie"),
                                                                                                            rec.pnick,
                                                                                                            rec.carebears+howmany))
        return 1

    def can_give_cookies(self,irc_msg,u,howmany):
        available_cookies = u.check_available_cookies(self.cursor,self.config)

        if howmany > available_cookies:
            reply="Silly, %s. You currently only have %s cookies to give out, but are trying to give out %s cookies. I'll bake you some new cookies on Monday morning." % (u.pnick, u.available_cookies, howmany)
            irc_msg.reply(reply)
            return False
        return True

    def show_status(self,irc_msg,u):
        available_cookies = u.check_available_cookies(self.cursor,self.config)

        reply="You have %d cookies left until next bakeday, %s"%(available_cookies,u.pnick)
        irc_msg.reply(reply)
