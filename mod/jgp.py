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

# Nothing alliance specific found in this module.
# qebab, 24/6/08.

class jgp(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,50)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(.*)")
        self.idre=re.compile(r"(\d{1,9})")
        self.usage=self.__class__.__name__ + ""
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
        params=m.group(1)
        m=self.planet_coordre.search(params)
        
        reply=""
        if m:
            x=m.group(1)
            y=m.group(2)
            z=m.group(3)
            
            p=loadable.planet(x=x,y=y,z=z)
            if not p.load_most_recent(self.conn,self.client,self.cursor):
                self.client.reply(prefix,nick,target,"No planet matching '%s:%s:%s' found"%(x,y,z))
                return 1

            #query="SELECT t1.tick AS tick,t1.nick,t1.scantype,t1.rand_id,t3.name,t2.amount"
            query="SELECT t3.x,t3.y,t3.z,t1.tick AS tick,t1.nick,t1.scantype,t1.rand_id,t2.mission,t2.fleet_size,t2.fleet_name,t2.landing_tick-t1.tick AS eta"
            query+=" FROM scan AS t1"
            query+=" INNER JOIN fleet AS t2 ON t1.id=t2.scan_id"
            query+=" INNER JOIN planet_dump AS t3 ON t2.owner_id=t3.id"
            query+=" WHERE t1.pid=%s AND t3.tick=(SELECT max_tick())"
            query+=" AND t1.id=(SELECT id FROM scan WHERE pid=t1.pid AND scantype='jgp'"
            query+=" ORDER BY tick DESC, id DESC LIMIT 1) ORDER BY eta ASC"
            #query+=" ORDER BY tick DESC LIMIT 1) ORDER BY eta ASC"
            self.cursor.execute(query,(p.id,))

            if self.cursor.rowcount < 1:
                if self.fallback(nick,username,host,target,prefix,p,None):
                    return 1
                else:
                    reply+="No JGP scans available on %s:%s:%s" % (p.x,p.y,p.z)

            else:
                reply+="Newest JGP scan on %s:%s:%s" % (p.x,p.y,p.z)
                
                prev=[]
                for s in self.cursor.dictfetchall():
                    prev.append("(%s:%s:%s %s | %s %s %s)" % (s['x'],s['y'],s['z'],s['fleet_name'],s['fleet_size'],s['mission'],s['eta']))
                    tick=s['tick']
                    rand_id=s['rand_id']
                    
                reply+=" (id: %s, pt: %s) " % (rand_id,tick)
                reply+=string.join(prev,' | ')
        else:
            m=self.idre.search(params)
            if not m:
                self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
                return 0
            
            rand_id=m.group(1)

            query="SELECT t4.x AS targ_x,t4.y AS targ_y,t4.z AS targ_z,t1.tick,t1.nick,t1.scantype,t1.rand_id,t2.fleet_size,t2.fleet_name,t2.landing_tick-t1.tick AS eta"
            query+= ",t5.x AS x,t5.y AS y,t5.z AS z"
            query+=" FROM scan AS t1"
            query+=" INNER JOIN fleet AS t2 ON t1.id=t2.scan_id"
            query+=" INNER JOIN planet_dump AS t4 ON t1.pid=t4.id"
            query+=" INNER JOIN planet_dump AS t5 ON t4.tick=t5.tick AND t2.owner_id=t5.id"
            query+=" WHERE t4.tick=(SELECT max_tick()) AND t1.rand_id=%s"
            self.cursor.execute(query,(rand_id,))

            if self.cursor.rowcount < 1:
                if self.fallback(nick,username,host,target,prefix,None,rand_id):
                    return 1
                else:
                    reply+="No JGP scans matching ID %s" % (rand_id,)
            else:
                reply+="Newest JGP scan on "

                prev=[]
                for s in self.cursor.dictfetchall():
                    prev.append("(%s:%s:%s %s size: %s eta: %s)" % (s['x'],s['y'],s['z'],s['fleet_name'],s['fleet_size'],s['eta']))
                    tick=s['tick']
                    x=s['targ_x']
                    y=s['targ_y']
                    z=s['targ_z']

                reply+="%s:%s:%s (id: %s, pt: %s) " % (x,y,z,rand_id,tick)
                reply+=string.join(prev,' | ')
        self.client.reply(prefix,nick,target,reply)
        return 1
                    
               
    def fallback(self,nick,username,host,target,prefix,planet,rand_id):
        query="SELECT rand_id FROM scan AS t1 "
        query+=" INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
        query+=" WHERE t3.tick = (SELECT max_tick())"
        
        args=()
        if planet:
            query+=" AND t3.id=%s"
            args+=(planet.id,)
        elif rand_id:
            query+=" AND t1.rand_id=%s"
            args+=(rand_id,)
        else:
            return 0
        query+=" ORDER BY t1.tick DESC LIMIT 1"
        
        self.cursor.execute(query,args)
        
        if self.cursor.rowcount < 1:
            return 0 # failure
        s=self.cursor.dictfetchone()
        self.client.reply(prefix,nick,target,"I can't see any fleets found matching this scan, but here's a URL you can try anyway: http://game.planetarion.com/showscan.pl?scan_id=%s"%(s['rand_id'],))
        
         
        return 1
