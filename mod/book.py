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

class book(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^\s+(\d+)[. :-](\d+)[. :-](\d+)\s+(\d+)(\s+(yes))?")
        self.usage=self.__class__.__name__ + " <x:y:z> (<eta>|<landing tick>)"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
            
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        x=m.group(1)
        y=m.group(2)
        z=m.group(3)
        when=int(m.group(4))
        override=m.group(6)

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        p=loadable.planet(x=x,y=y,z=z)
        if not p.load_most_recent(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"No planet matching '%s:%s:%s' found"%(x,y,z))
            return 1
        else:
            i=loadable.intel(pid=p.id)
            if not i.load_from_db(self.conn,self.client,self.cursor):
                pass
            else:
                if i and i.alliance and i.alliance.lower()=='ascendancy':
                    self.client.reply(prefix,nick,target,"%s:%s:%s is %s in Ascendancy. Quick, launch before they notice the highlight."%(x,y,z,i.nick or 'someone'))
                    return 0 
        curtick=self.current_tick()
        tick=-1
        eta=-1
        
        if when < 80:
            tick=curtick+when
            eta=when
        elif when < curtick:
            self.client.reply(prefix,nick,target,"Can not book targets in the past. You wanted tick %s, but current tick is %s."%(when,curtick))
            return 1
        else:
            tick=when
            eta=tick-curtick
        if tick > 32767:
            tick=32767


        args=()
        query="SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid, t2.pnick AS pnick, t2.userlevel AS userlevel, t3.x AS x, t3.y AS y, t3.z AS z"
        query+=" FROM target AS t1"
        query+=" INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
        query+=" LEFT JOIN user_list AS t2 ON t1.uid=t2.id"
        query+=" WHERE"
        query+=" t1.tick > %s"
        query+=" AND t3.tick = (SELECT MAX(tick) FROM updates) AND t3.x=%s AND t3.y=%s"
        query+=" AND t3.z=%s"
        
        self.cursor.execute(query,(tick,x,y,z))

        if self.cursor.rowcount > 0 and not override:
            reply="There are already bookings for that target after landing pt %s (eta %s). To see status on this target, do !status %s:%s:%s." % (tick,eta,x,y,z)
            reply+=" To force booking at your desired eta/landing tick, use !book %s:%s:%s %s yes (Bookers:" %(x,y,z,tick)
            prev=[]
            for r in self.cursor.dictfetchall():
                owner="nick:"+r['nick']
                if r['pnick']:
                    owner="user:"+r['pnick']
                    prev.append("(%s %s)" % (r['tick'],owner))
            reply+=" "+string.join(prev,', ')
            reply+=" )"
            self.client.reply(prefix,nick,target,reply)
            return 1
        
        uid=None
        if user:
            u=loadable.user(pnick=user)
            if u.load_from_db(self.conn,self.client,self.cursor):
                uid=u.id

        query="INSERT INTO target (nick,pid,tick,uid) VALUES (%s,%s,%s,%s)"
        try:
            self.cursor.execute(query,(nick,p.id,tick,uid))
            if uid:
                reply="Booked landing on %s:%s:%s tick %s for user %s" % (p.x,p.y,p.z,tick,user)
            else:
                reply="Booked landing on %s:%s:%s tick %s for nick %s" % (p.x,p.y,p.z,tick,nick)
        except psycopg.IntegrityError:
            query="SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid, t2.pnick AS pnick, t2.userlevel AS userlevel "
            query+=" FROM target AS t1 LEFT JOIN user_list AS t2 ON t1.uid=t2.id "
            query+=" WHERE t1.pid=%s AND t1.tick=%s"

            self.cursor.execute(query,(p.id,tick))
            book=self.cursor.dictfetchone()
            if not book:
                raise Exception("Integrity error? Unable to booking for pid %s and tick %s"%(p.id,tick))
            if book['pnick']:
                reply="Target %s:%s:%s is already booked for landing tick %s by user %s" % (p.x,p.y,p.z,book['tick'],book['pnick'])
            else:
                reply="Target %s:%s:%s is already booked for landing tick %s by nick %s" % (p.x,p.y,p.z,book['tick'],book['nick'])
        except:
            raise

        self.client.reply(prefix,nick,target,reply)

        return 1
