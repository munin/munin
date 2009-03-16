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

# This module doesn't have anything alliance specific as far as I can tell.
# qebab, 24/6/08.

import re
from munin import loadable

class exile(loadable.loadable):
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,1)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^(.*)")
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



        # do stuff here
	query = "SELECT planets,count(*) AS count FROM "
	query+= " (SELECT  x AS x,y AS y,count(*) AS planets from planet_dump"
	query+= " WHERE tick = (SELECT max_tick()) AND x < 200"
	query+= " GROUP BY x,y ORDER BY count(*) DESC) AS foo"
	query+= " GROUP BY planets ORDER BY planets ASC"

	reply=""
	self.cursor.execute(query)
	if self.cursor.rowcount<1:
	    reply="There is no spoon"
	else:
	    res=self.cursor.dictfetchall()
	    gals=0
	    bracket=0
	    max_planets=0

	    for r in res:
		gals+=r['count']
	    bracket=int(gals*.2)
	    for r in res:
		bracket-=r['count']
		if bracket < 0:
                    rest_gals=bracket+r['count']
                    total_rest_gals=r['count']
                    rest_planets=r['planets']
		    break
		max_planets=r['planets']

	    reply="Total galaxies: %s Maximum planets to guarantee a galaxy is in the exile bracket: %s" % (gals,max_planets)
            reply+=" | Also in the bracket: %s of %s galaxies with %s planets."%(rest_gals,total_rest_gals,rest_planets)

	irc_msg.reply(reply)

        return 1
