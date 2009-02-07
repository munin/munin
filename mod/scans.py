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

# Nothing alliance specific in this module as far as I can tell.
# qebab, 24/6/08.

class scans(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,50)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + " <x:y:z>"
        self.helptext=None

    def execute(self,nick,host,target,prefix,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        
        m=self.planet_coordre.search(m.group(1))
        if  m:
           
            x=m.group(1)
            y=m.group(2)
            z=m.group(3)
            
            p=loadable.planet(x=x,y=y,z=z)
            if not p.load_most_recent(irc_msg.client,self.cursor):
                irc_msg.reply("No planet matching '%s:%s:%s' found"%(x,y,z))
                return 1
            
            query="SELECT scantype,max(tick) AS latest,count(*) AS count FROM scan WHERE pid=%s GROUP BY scantype"
            self.cursor.execute(query,(p.id,))
            
            reply=""
            if self.cursor.rowcount < 1:
                reply+="No scans available on %s:%s:%s" % (p.x,p.y,p.z)
                
            else:
                reply+="scans for %s:%s:%s -" % (p.x,p.y,p.z)
                prev=[]
                for p in self.cursor.dictfetchall():
                    prev.append("(%d %s, latest pt%s)" % (p['count'],p['scantype'],p['latest']))
                    
                reply+=" "+string.join(prev,', ')
            
                
            irc_msg.reply(reply)

        else:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        return 1
