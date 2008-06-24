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

class news(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,50)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(.*)")
        self.idre=re.compile(r"(\d{1,9})")
        self.usage=self.__class__.__name__ + " <x:y:z>" 
        self.helptext=["Looks up recent news scan IDs on a planet"]

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
            
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0
        
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        # assign param variables    
        params=m.group(1)
        m=self.planet_coordre.search(params)
        reply=""
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        x=m.group(1)
        y=m.group(2)
        z=m.group(3)
        p=loadable.planet(x=x,y=y,z=z)

        if not p.load_most_recent(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"No planet matching '%s:%s:%s' found"%(x,y,z))
            return 1

        query="SELECT tick,nick,scantype,rand_id,tick"
        query+=" FROM scan AS t1"
        query+=" WHERE t1.pid=%s AND scantype='news' ORDER BY tick DESC"
        self.cursor.execute(query,(p.id,))

        s=self.cursor.dictfetchone()
        if s:        
            reply="Latest news scan on %s:%s:%s - http://game.planetarion.com/showscan.pl?scan_id=%s"%(x,y,z,s['rand_id'])
        else:
            reply="No news available on %s:%s:%s"%(x,y,z)
        self.client.reply(prefix,nick,target,reply)

        return 1

