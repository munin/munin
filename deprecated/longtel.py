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

class longtel(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s*(\d+)[. :-](\d+)")
        self.usage=self.__class__.__name__ + " x:y"
	self.helptext=['Shows the long version of intel on a galaxy.']

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

        x=int(m.group(1))
        y=int(m.group(2))

        self.exec_gal(irc_msg,x,y)
        # do stuff here

        return 1

    def exec_gal(self,irc_msg,x,y):
        query="SELECT t2.id AS id, t1.id AS pid, t1.x AS x, t1.y AS y, t1.z AS z, t2.nick AS nick, t2.fakenick AS fakenick, t2.defwhore AS defwhore, t2.gov AS gov, t2.bg AS bg, t2.covop AS covop, t2.alliance_id AS alliance_id, t2.relay AS relay, t2.reportchan AS reportchan, t2.scanner AS scanner, t2.distwhore AS distwhore, t2.comment AS comment, t3.name AS alliance FROM planet_dump as t1, intel as t2 LEFT JOIN alliance_canon AS t3 ON t2.alliance_id=t3.id WHERE tick=(SELECT MAX(tick) FROM updates) AND t1.id=t2.pid AND x=%s AND y=%s ORDER BY y,z,x"
        self.cursor.execute(query,(x,y))

        replied_to_request = False
        for d in self.cursor.fetchall():
            x=d['x']
            y=d['y']
            z=d['z']
            i=loadable.intel(pid=d['pid'],nick=d['nick'],fakenick=d['fakenick'],defwhore=d['defwhore'],gov=d['gov'],bg=d['bg'],
                             covop=d['covop'],alliance=d['alliance'],relay=d['relay'],reportchan=d['reportchan'],
                             scanner=d['scanner'],distwhore=d['distwhore'],comment=d['comment'])
            if not i.is_empty():
                replied_to_request = True
                reply="Information stored for %s:%s:%s - "% (x,y,z)
                reply+=i.__str__()
                irc_msg.reply(reply)

        if not replied_to_request:
            irc_msg.reply("No information stored for galaxy %s:%s" % (x,y))
        return 1
