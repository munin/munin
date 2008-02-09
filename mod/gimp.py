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

class gimp(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^(\s+(\S+))?")
        self.usage=self.__class__.__name__ + " <gimp's pnick>"
        
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
        gimp=m.group(2)
        
        # do stuff here
        reply=""
        if gimp:
            query="SELECT (36-(EXTRACT(DAYS FROM now()-t1.timestamp)*24+EXTRACT(HOUR FROM now() - t1.timestamp))) AS left,t1.pnick AS gimp,t1.comment AS comment,t2.pnick AS sponsor FROM sponsor AS t1 INNER JOIN user_list AS t2 ON t1.sponsor_id=t2.id WHERE t1.pnick ILIKE %s"
            self.cursor.execute(query,(gimp,))
            if self.cursor.rowcount < 1:
                reply+="No gimps matching '%s'. This command requires a full match to display results." % (gimp,)
            else:
                r=self.cursor.dictfetchone()
                reply+="Gimp: %s, Sponsor: %s, Waiting: %d more hours, Comment: %s" % (r['gimp'],r['sponsor'],r['left'],r['comment'])
        else:
            query="SELECT (36-(EXTRACT(DAYS FROM now()-t1.timestamp)*24+EXTRACT(HOUR FROM now() - t1.timestamp))) AS left,t1.pnick AS gimp,t2.pnick AS sponsor FROM sponsor AS t1 INNER JOIN user_list AS t2 ON t1.sponsor_id=t2.id ORDER BY t1.pnick ASC"
            self.cursor.execute(query)
            if self.cursor.rowcount < 1:
                reply+="There are currently no gimps up for recruit"
            else:
                reply+="Current gimps (with sponsor):"

                prev=[]
                for p in self.cursor.dictfetchall():
                    prev.append("(gimp:%s,sponsor:%s (%d hours left))" % (p['gimp'],p['sponsor'],p['left']))
                reply+=" "+string.join(prev,', ')

            
        
        self.client.reply(prefix,nick,target,reply)
        
        return 1
                                                                                                                                            
