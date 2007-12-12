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

class afford(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\d+)[. :-](\d+)[. :-](\d+)\s+(\S+)")
        self.idre=re.compile(r"(\d{1,9})")
        self.usage=self.__class__.__name__ + " <x:y:z> <shipname>"
        self.helptext=None

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
        reply=""
        x=m.group(1)
        y=m.group(2)
        z=m.group(3)
        ship_name=m.group(4)
        
        p=loadable.planet(x=x,y=y,z=z)
        if not p.load_most_recent(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"No planet matching '%s' found"%(param,))
            return 1
        
        query="SELECT tick,nick,scantype,rand_id,timestamp,roid_metal,roid_crystal,roid_eonium,res_metal,res_crystal,res_eonium"
        query+=" FROM scan AS t1 INNER JOIN planet AS t2 ON t1.id=t2.scan_id"
        query+=" WHERE t1.pid=%s ORDER BY timestamp DESC"
        self.cursor.execute(query,(p.id,))
        
        if self.cursor.rowcount < 1:
            reply+="No planet scans available on %s:%s:%s" % (p.x,p.y,p.z)
        else:
            s=self.cursor.dictfetchone()
            tick=s['tick']
            res_m=int(s['res_metal'])
            res_c=int(s['res_crystal'])
            res_e=int(s['res_eonium'])
            rand_id=s['rand_id']
            
            query="SELECT name,int4smaller(int4smaller(floor(%d/metal)::int4,floor(%d/crystal)::int4),floor(%d/eonium)::int4) AS buildable FROM ship WHERE name ILIKE %s LIMIT 1"
            self.cursor.execute(query,(res_m,res_c,res_e,'%'+ship_name+'%'))
                        
            if self.cursor.rowcount<1:
                reply="%s is not a ship" % (ship_name,)
            else:
                s=self.cursor.dictfetchone()
                reply+="Newest planet scan on %s:%s:%s (id: %s, pt: %s)" % (p.x,p.y,p.z,rand_id,tick)
                reply+=" can purchase %s: %s | Feudalism: %s"%(s['name'],s['buildable'],int(s['buildable']*1.1765))
                #Dictatorship: %s"%(s['name'],s['buildable'],int(s['buildable']*1.1765),
                #                                                                int(s['buildable']*.9524))
                

        self.client.reply(prefix,nick,target,reply)
        return 1
