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

# Nothing ascendancy/jester specific found here.
# qebab, 24/6/08.

from munin import loadable

class whois(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + ""
	self.helptext=None

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
        search=m.group(1)

        # do stuff here

        if search.lower() == 'munin':
            irc_msg.reply("I am Munin. Hear me roar.")
            return 1

        query="SELECT pnick,sponsor,invites,carebears"
        query+=" FROM user_list"
        query+=" WHERE pnick ilike %s"
        query+=" AND userlevel >= 100"

        self.cursor.execute(query,(search,))

        reply=""
        if self.cursor.rowcount < 1:
            self.cursor.execute(query,('%'+search+'%',))

        r=self.cursor.dictfetchone()

        if not r:
            reply+="No members matching '%s'"%(search,)
        else:
            u=loadable.user(pnick=r['pnick'])
            u.load_from_db( self.cursor)
            if r['pnick'] == irc_msg.user:
                reply+="You are %s. Your sponsor is %s. Your Munin number is %s. You have %d %s."
            else:
                reply+="Information about %s: Their sponsor is %s. Their Munin number is %s. They have %d %s."
            reply=reply%(r['pnick'],r['sponsor'],self.munin_number_to_output(u),r['carebears'],self.pluralize(r['carebears'],"carebear"))

        irc_msg.reply(reply)

        return 1
    def munin_number_to_output(self,u):
        number=u.munin_number( self.cursor, self.config)
        if number:
            return number
        else:
            return "a kabajillion"
