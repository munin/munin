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



class surprisesex(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + " [<[x:y[:z]]|[alliancename]>]"
	self.helptext=None

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0
    

        m=self.paramre.search(m.group(1))
        if not m or not m.group(1):
            u=loadable.user(pnick=user)
            if not u.load_from_db(self.conn,self.client,self.cursor):
                self.client.reply(prefix,nick,target,"Usage: %s (you must be registered for automatic lookup)" % (self.usage,))
                return 1
            if u.planet:
                reply=self.surprise(x=u.planet.x,y=u.planet.y,z=u.planet.z)
                self.client.reply(prefix,nick,target,reply)
            else:
                self.client.reply(prefix,nick,target,"Usage: %s (you must be registered for automatic lookup)" % (self.usage,))
            return 0

        # assign param variables 
        param=m.group(1)
        m=self.coordre.search(param)
        if m:
            x=m.group(1)
            y=m.group(2)
            z=m.group(4)

            if z:
                p=loadable.planet(x=x,y=y,z=z)
                if not p.load_most_recent(self.conn,self.client,self.cursor):
                    self.client.reply(prefix,nick,target,"No planet matching '%s' found"%(param,))
                    return 1
                reply=self.surprise(x=p.x,y=p.y,z=p.z)

                self.client.reply(prefix,nick,target,reply)
                return 1
            else:
                g=loadable.galaxy(x=x,y=y)
                if not g.load_most_recent(self.conn,self.client,self.cursor):
                    self.client.reply(prefix,nick,target,"No galaxy matching '%s' found"%(param,))
                    return 1
                reply=self.surprise(x=g.x,y=g.y)
                self.client.reply(prefix,nick,target,reply)
                return 1
        
        a=loadable.alliance(name=param.strip())
        if not a.load_most_recent(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"No alliance matching '%s' found" % (param,))
            return 1
        reply=self.surprise(alliance=a.name)
        self.client.reply(prefix,nick,target,reply)

        return 1

    def cap(self,text):
        if len(text)>3:
           return text.title()
        else:
            return text.upper()

    def surprise(self,x=None,y=None,z=None,alliance=None):
        args=()
        query="SELECT COALESCE(lower(t2.alliance),'unknown') AS alliance,count(COALESCE(lower(t2.alliance),'unknown')) AS attacks "
        query+=" FROM planet_canon AS t1"
        query+=" INNER JOIN fleet AS t3 ON t1.id=t3.owner"
        query+=" LEFT JOIN intel AS t2 ON t3.owner=t2.pid"
        query+=" INNER JOIN planet_dump AS t4 ON t4.id=t3.target"
        query+=" INNER JOIN intel AS t5 ON t3.target=t5.pid"
        query+=" WHERE mission = 'attack'"
        query+=" AND t4.tick=(SELECT max_tick())"

        if x and y:
            query+=" AND t4.x=%s AND t4.y=%s"
            args+=(x,y)
        if z:
            query+=" AND t4.z=%s"
            args+=(z,)
        
        if alliance:
            query+=" AND t5.alliance ilike %s"
            args+=('%'+alliance+'%',)
        
        query+=" GROUP BY lower(t2.alliance)"
        query+=" ORDER BY count(lower(t2.alliance)) DESC"

        self.cursor.execute(query,args)
        attackers=self.cursor.dictfetchall()
        if not len(attackers):
            reply="No fleets found targeting"
            if x and y:
                reply+=" coords %s:%s"%(x,y)
            if z:
                reply+=":%s"%(z,)
            if alliance:
                reply+=" alliance %s"%(alliance,)
        else:
            reply="Top attackers on"
            if x and y:
                reply+=" coords %s:%s"%(x,y)
            if z:
                reply+=":%s"%(z,)
            if alliance:
                reply+=" alliance %s"%(alliance,)
            reply+=" are "
            i=0
            prev=[]
            for a in attackers:
               if i>4:
                   break
               else:
                   i+=1
               prev.append("%s - %s"%(self.cap(a['alliance'] or 'unknown'),a['attacks']))
               
            reply+=string.join(prev," | ")

        return reply
    
        """
select lower(t2.alliance),count(lower(t2.alliance)) 
from planet_canon AS t1 
inner join fleet AS t3 on t1.id=t3.owner 
left join intel AS t2 on t3.owner=t2.pid 
inner join planet_canon as t4 on t4.id=t3.target
inner join intel AS t5 on t3.target=t5.pid
WHERE 
t5.alliance ilike '%asc%'
and mission = 'attack' 
group by lower(t2.alliance);
"""
