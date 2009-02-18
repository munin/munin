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



class letmein(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,0)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)\s+(\S+)")
        self.usage=self.__class__.__name__ + " <pnick> <password>"
	self.helptext=["Give your pnick and password in PM to get invited into #%s. This command is for when P is down."%(self.config.get('Auth','home'),)]

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        public=re.match(r"(#\S+)",irc_msg.target,re.I)
        if public:
            irc_msg.reply("Don't use this command in public you shit")

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        auther=m.group(1)
        passy=m.group(2)

        query="SELECT pnick, userlevel FROM user_list"
        query+=" WHERE pnick ilike %s AND passwd = MD5(MD5(salt) || MD5(%s))"


        self.cursor.execute(query,(auther,passy))
        if self.cursor.rowcount == 1:
            r=self.cursor.dictfetchone()
            if r['userlevel'] >= 100:
                irc_msg.client.wline("INVITE %s #%s"%(irc_msg.nick,self.config.get('Auth','home')))
                irc_msg.reply("Now get in, bitch")
                irc_msg.client.privmsg("#%s"%(self.config.get('Auth','home'),),"%s is entering the channel under nick %s, quick everyone, hide!"%(auther,irc_msg.nick))
        else:
            irc_msg.reply( "No.")
        # do stuff here

        return 1
