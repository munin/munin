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

class showdef(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s*(\S+)?")
        self.usage=self.__class__.__name__ + ""
	self.helptext=None

    def execute(self,user,access,irc_msg):
        m=self.commandre.search(irc_msg.command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        name=m.group(1)
        if name:
            u=self.load_user_from_pnick(name)
        else:
            u=self.load_user_from_pnick(irc_msg.user)
        if not u or u.userlevel < 100:
            irc_msg.reply("No members matching %s found"%(name,))
            return

        if self.cursor.rowcount < 1:
            irc_msg.reply("%s is either a lazy pile of shit that hasn't entered any ships for def, or a popular whore who's already turned their tricks."%(u.pnick,))
            return
        
        ships=u.get_fleets(self.cursor)

        reply="%s def info: fleetcount %s, updated: %s (%s), ships: " %(u.pnick,u.fleetcount,u.fleetupdated,u.fleetupdated-self.current_tick())
        reply+=", ".join(map(lambda x: "%s %s"%(self.format_real_value(x['ship_count']),x['ship']),ships))
        reply+=" comment: %s"%(u.fleetcomment,)
        irc_msg.reply(reply)
        return 1
