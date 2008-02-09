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

class surface(loadable.loadable):
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
                self.client.reply(prefix,nick,target,"No planet matching '%s' found"%(param,))
                return 1
            
            query="SELECT t2.id AS id,tick,nick,scantype,rand_id,light_factory,medium_factory,heavy_factory,wave_amplifier,wave_distorter"
            query+=",metal_refinery,crystal_refinery,eonium_refinery,research_lab,finance_centre,security_centre"
            query+=" FROM scan AS t1 INNER JOIN structure AS t2 ON t1.id=t2.scan_id"
            query+=" WHERE t1.pid=%s ORDER BY tick DESC"
            self.cursor.execute(query,(p.id,))
                
            if self.cursor.rowcount < 1:
                reply+="No surface scans available on %s:%s:%s" % (p.x,p.y,p.z)
            else:
                s=self.cursor.dictfetchone()
                query="SELECT light_factory+medium_factory+heavy_factory+wave_amplifier+wave_distorter+metal_refinery+crystal_refinery+eonium_refinery+research_lab+finance_centre+security_centre AS total FROM structure WHERE id=%s"
                self.cursor.execute(query,(s['id'],))
                total=self.cursor.dictfetchone()['total']
                reply+="Newest surface scan on %s:%s:%s (id: %s, pt: %s)" % (p.x,p.y,p.z,s['rand_id'],s['tick'])
                #reply+=" Roids: (m:%s, c:%s, e:%s) | Resources: (m:%s, c:%s, e:%s)" % (s['roid_metal'],s['roid_crystal'],s['roid_eonium'],s['res_metal'],s['res_crystal'],s['res_eonium'])
                reply+=" LFac: %s, MFac: %s, HFac: %s, Amp: %s, Dist: %s, MRef: %s, CRef: %s, ERef: %s, ResLab: %s (%s%%), FC: %s, Sec: %s (%s%%) " % (s['light_factory'],s['medium_factory'],
                                                                                                                                                       s['heavy_factory'],s['wave_amplifier'],
                                                                                                                                                       s['wave_distorter'],s['metal_refinery'],
                                                                                                                                                       s['crystal_refinery'],s['eonium_refinery'],
                                                                                                                                                       s['research_lab'],
                                                                                                                                                       int(float(s['research_lab'])/total*100),
                                                                                                                                                       s['finance_centre'],
                                                                                                                                                       s['security_centre'],
                                                                                                                                                       int(float(s['security_centre'])/total*100))
                i=0
                reply+=" Older scans: "
                prev=[]
                for s in self.cursor.dictfetchall():
                    i+=1
                    if i > 4:
                        break
                    prev.append("(%s,pt%s)" % (s['rand_id'],s['tick']))
                reply+=string.join(prev,', ')

        else:
            m=self.idre.search(params)
            if not m:
                self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
                return 0

            rand_id=m.group(1)
            #query="SELECT x,y,z,t1.tick AS tick,nick,scantype,rand_id,timestamp,roid_metal,roid_crystal,roid_eonium,res_metal,res_crystal,res_eonium"
            query="SELECT x,y,z,t2.id AS id,t1.tick AS tick,nick,scantype,rand_id,light_factory,medium_factory,heavy_factory,wave_amplifier,wave_distorter"
            query+=",metal_refinery,crystal_refinery,eonium_refinery,research_lab,finance_centre,security_centre"            
            query+=" FROM scan AS t1 INNER JOIN structure AS t2 ON t1.id=t2.scan_id"
            query+=" INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
            query+=" WHERE t3.tick=(SELECT MAX(tick) FROM updates) AND t1.rand_id=%s ORDER BY tick DESC"
            self.cursor.execute(query,(rand_id,))
        
            if self.cursor.rowcount < 1:
                reply+="No surface scans matching ID %s" % (rand_id,)
            else:
                s=self.cursor.dictfetchone()
                query="SELECT light_factory+medium_factory+heavy_factory+wave_amplifier+wave_distorter+metal_refinery+crystal_refinery+eonium_refinery+research_lab+finance_centre+security_centre AS total FROM structure WHERE id=%s"
                self.cursor.execute(query,(s['id'],))
                total=self.cursor.dictfetchone()['total']                
                reply+="Surface scan on %s:%s:%s (id: %s, pt: %s)" % (s['x'],s['y'],s['z'],s['rand_id'],s['tick'])
                #reply+=" Roids: (m:%s, c:%s, e:%s) | Resources: (m:%s, c:%s, e:%s)" % (s['roid_metal'],s['roid_crystal'],s['roid_eonium'],s['res_metal'],s['res_crystal'],s['res_eonium'])
                
                reply+=" LFac: %s, MFac: %s, HFac: %s, Amp: %s, Dist: %s, MRef: %s, CRef: %s, ERef: %s, ResLab: %s (%s%%), FC: %s, Sec: %s (%s%%) " % (s['light_factory'],s['medium_factory'],
                                                                                                                                                       s['heavy_factory'],s['wave_amplifier'],
                                                                                                                                                       s['wave_distorter'],s['metal_refinery'],
                                                                                                                                                       s['crystal_refinery'],s['eonium_refinery'],
                                                                                                                                                       s['research_lab'],
                                                                                                                                                       int(float(s['research_lab'])/total*100),
                                                                                                                                                       s['finance_centre'],
                                                                                                                                                       s['security_centre'],
                                                                                                                                                       int(float(s['security_centre'])/total*100))
        self.client.reply(prefix,nick,target,reply)
        
                       

        # do stuff here

        return 1
