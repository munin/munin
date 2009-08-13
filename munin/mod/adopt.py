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

class adopt(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + "<pnick>"
        self.helptext=None

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
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        
        # assign param variables
        adoptee=m.group(1)

        if adoptee.lower() == self.config.get('Connection','nick').lower():
            irc_msg.reply("Fuck off you stupid twat, stop trying to be a clever shit.")
            return 1

        if adoptee.lower() == u.pnick.lower():
            irc_msg.reply("Stop wanking your own dick and find a daddy to do it for you, retard.")
            return 1

        a=loadable.user(pnick=adoptee)
        a.load_from_db( self.cursor)
        if not a.id or a.userlevel < 100:
            irc_msg.reply("No members matching '%s'"%(adoptee,))
            return 1

        s=loadable.user(pnick=a.pnick)
        s.load_from_db( self.cursor)
        if s.id and s.userlevel >= 100:
            irc_msg.reply("%s already has a daddy you filthy would-be kidnapper!"%(a.pnick,))
            return 1

        query="UPDATE user_list"
        query+=" SET sponsor = %s"
        query+=" WHERE id = %s"
        self.cursor.execute(query,(u.pnick,a.id,))

        irc_msg.reply("Congratulations! You're now the proud father of a not-so newly born %s!"%(a.pnick,))
        return 1
