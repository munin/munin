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
import munin.loadable as loadable

class alias(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,1)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s*(\S{2,15})?")
        self.usage=self.__class__.__name__ + " <alias> (at most 15 characters)"
	self.helptext=['Set an alias that maps to your pnick, useful if you have a different nick than your pnick and people use autocomplete.'] 

    def execute(self,user,access,irc_msg):
        m=self.commandre.search(irc_msg.command)
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

        alias=m.group(1)
        if not alias:
            irc_msg.reply("You are %s, your alias is %s"%(u.pnick,u.alias_nick))
        else:
            self.update_alias(u,alias,irc_msg)
        return 1

    def update_alias(self,u,alias,irc_msg):
        query="SELECT pnick FROM user_list WHERE pnick ilike %s"
        self.cursor.execute(query,(alias,))
        if self.cursor.rowcount > 0:
            irc_msg.reply("Your alias is already in use or is someone else's pnick (not allowed). Tough noogies.")
            return
        try:
            query="UPDATE user_list SET alias_nick = %s WHERE pnick ilike %s"
            self.cursor.execute(query,(alias,u.pnick))
            if self.cursor.rowcount > 0:
                irc_msg.reply("Update alias for %s (that's you) to %s"%(u.pnick,alias))
            else:
                irc_msg.reply("If you see this message you are a winner. Fuck you.")
        except:
            irc_msg.reply("Your alias is already in use or is someone else's pnick (not allowed). Tough noogies.")
