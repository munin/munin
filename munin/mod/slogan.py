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

# This module has nothing alliance specific as far as I can tell.
# qebab, 24/6/08.

import re
from munin import loadable

class slogan(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,1)
        self.paramre=re.compile(r"^\s+(.*)$")
        self.usage=self.__class__.__name__ + ""

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        params=None
        if m:
            params=m.group(1)


        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        args=()
        query="SELECT slogan FROM slogan WHERE 1=1"

        if params:
            query+=" AND slogan ILIKE %s"
            args+=("%"+params+"%",)

        query+=" ORDER BY RANDOM()"
        self.cursor.execute(query,args)

        reply=""
        if self.cursor.rowcount == 0:
            reply+="No slogans matching '%s'" % (params,)
        else:
            res=self.cursor.dictfetchone()
            reply+="%s" %(res['slogan'],)
            if self.cursor.rowcount > 1 and params:
                reply+=" (%d more slogans match this search)" % (self.cursor.rowcount - 1)

        irc_msg.reply(reply)


        # do stuff here

        return 1

