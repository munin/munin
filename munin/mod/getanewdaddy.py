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

# I have removed everything alliance specific that I could find in this module.
# qebab, 24/6/08.

import re
from munin import loadable

class getanewdaddy(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + " <pnick>"
        self.helptext=['This command is used when you no longer wish to be sponsor for a person. Their access to #%s will be removed and their Munin access will be lowered to "galmate" level.' % self.config.get('Auth', 'home'),
                       "Anyone is free to sponsor the person back under the usual conditions. This isn't a kick and it's not final."]
        #self.helptext=['This command is used to vote someone out of the alliance. Your vote is logged and everyone can see what a cunt you are.']

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables

        voter=loadable.user(pnick=irc_msg.user)
        if not voter.load_from_db(self.cursor):
            irc_msg.reply("You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
            return 1


        idiot=loadable.user(pnick=m.group(1))
        if not idiot.load_from_db(self.cursor):
            irc_msg.reply("That idiot doesn't exist")
            return 1

        # do stuff here

        if access < 1000 and idiot.sponsor.lower() != voter.pnick.lower():
            reply="You are not %s's sponsor"%(idiot.pnick,)
            irc_msg.reply(reply)
            return 1

        query="UPDATE user_list SET userlevel = 1 WHERE id = %s"
        self.cursor.execute(query,(idiot.id,))
        irc_msg.client.privmsg('p','remuser #%s %s'%(self.config.get('Auth', 'home'), idiot.pnick,))
        irc_msg.client.privmsg('p',"ban #%s *!*@%s.users.netgamers.org Your sponsor doesn't like you anymore"%(self.config.get('Auth', 'home'), idiot.pnick,))

        if idiot.sponsor != voter.pnick:
            irc_msg.client.privmsg('p',"note send %s Some admin has removed you from %s for whatever reason. If you still wish to be a member, go ahead and find someone else to sponsor you back."%(idiot.pnick, self.config.get('Auth', 'alliance')))
            reply="%s has been reduced to level 1 and removed from the channel. %s is no longer %s's sponsor. If anyone else would like to sponsor that person back, they may."%(idiot.pnick,idiot.sponsor,idiot.pnick)
        else:
            irc_msg.client.privmsg('p',"note send %s Your sponsor (%s) no longer wishes to be your sponsor for %s. If you still wish to be a member, go ahead and find someone else to sponsor you back."%(idiot.pnick,voter.pnick, self.config.get('Auth', 'alliance')))
            reply="%s has been reduced to level 1 and removed from the channel. You are no longer %s's sponsor. If anyone else would like to sponsor that person back, they may."%(idiot.pnick,idiot.pnick)
        irc_msg.reply(reply)
        return 1
