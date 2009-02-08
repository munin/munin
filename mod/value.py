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

# Nothing ascendancy/jester specific found here.
# qebab, 24/6/08.

class value(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,1)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\d+)[. :-](\d+)[. :-](\d+)\s+(\d+)")
        self.usage=self.__class__.__name__ + ""
        self.helptext=None

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        params=m.group(1)
        m=self.paramre.search(params)
        if m:
            x=m.group(1)
            y=m.group(2)
            z=m.group(3)
            tick=m.group(4)

            p=loadable.planet(x=x,y=y,z=z)
            if not p.load_most_recent(irc_msg.client,self.cursor):
                irc_msg.reply("No planet matching '%s:%s:%s' found"%(x,y,z))
                return 1
                                            
            query="SELECT t1.value,t1.value-t2.value AS vdiff,t1.size-t2.size AS sdiff"
            query+=" FROM planet_dump AS t1"
            query+=" INNER JOIN planet_dump AS t2"
            query+=" ON t1.id=t2.id AND t1.tick-1=t2.tick"
            query+=" WHERE t1.tick=%s AND t1.id=%s"

            reply=""
            
            self.cursor.execute(query,(tick,p.id))
            if self.cursor.rowcount<1:
                reply+="No data for %s:%s:%s on tick %s" % (p.x,p.y,p.z,tick)
            else:
                x=self.cursor.dictfetchone()
                
                reply+="Value on pt%s for %s:%s:%s: " % (tick,p.x,p.y,p.z)
                reply+="value: %s (%s%s) " % (x['value'],["+","-"][x['vdiff']<0],abs(x['vdiff']))
                if x['sdiff']!=0:
                    reply+="roids: %s%s" % (["+","-"][x['sdiff']<0],abs(x['sdiff']))
            irc_msg.reply(reply)
            return 1
            

        m=self.planet_coordre.search(params)
        if  m:
            x=m.group(1)
            y=m.group(2)
            z=m.group(3)

            p=loadable.planet(x=x,y=y,z=z)
            if not p.load_most_recent(irc_msg.client,self.cursor):
                irc_msg.reply("No planet matching '%s:%s:%s' found"%(x,y,z))
                return 1

            #query="SELECT tick,t1.value,t1.value-t2.value AS diff FROM planet_dump AS t1 INNER JOIN planet_dump AS t2 ON
            query="SELECT t1.tick,t1.value,t1.value-t2.value AS vdiff,t1.size-t2.size AS sdiff"
            query+=" FROM planet_dump AS t1"
            query+=" INNER JOIN planet_dump AS t2"
            query+=" ON t1.id=t2.id AND t1.tick-1=t2.tick" 
            query+=" WHERE t1.tick>(SELECT max_tick()-16) AND t1.id=%s"
            query+=" ORDER BY t1.tick ASC"

            self.cursor.execute(query,(p.id,))

            reply=""
            
            if self.cursor.rowcount<1:
                reply+="No data for %s:%s:%s" % (p.x,p.y,p.z)
            else:
                results=self.cursor.dictfetchall()
                
                reply+="Value in the last 15 ticks on %s:%s:%s: " % (p.x,p.y,p.z)
                
                info=map(lambda x: "pt%s %s (%s%s)" % (x['tick'],self.format_value(x['value']*100),["+","-"][x['vdiff']<0],
                                                         self.format_value(abs(x['vdiff']*100)))+
                         [" roids:"+["+","-"][x['sdiff']<0]+str(abs(x['sdiff'])),""][x['sdiff']==0],results)
                
                print info
                reply+=str.join(' | ',info)
            irc_msg.reply(reply)

            
        # assign param variables 
        

        # do stuff here

        return 1
