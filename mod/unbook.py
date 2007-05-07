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

class unbook(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,50)
        self.paramre=re.compile(r"^\s+(\d+)[. :-](\d+)[. :-](\d+)(\s+(\d+))?(\s+(yes))?")
        self.usage=self.__class__.__name__ + " <x:y:z> [<eta>|<landing tick>] [yes]"
        
    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        
        # assign param variables
        when=None
        x=m.group(1)
        y=m.group(2)
        z=m.group(3)
        when=m.group(5)
        if when: when=int(when)
        override=m.group(7)
        
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        curtick=self.current_tick()
        tick=-1
        eta=-1

        p=loadable.planet(x=x,y=y,z=z)
        if not p.load_most_recent(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"No planet matching '%s:%s:%s' found"%(x,y,z))
            return 1

        u=loadable.user(pnick=user)
        if not u.load_from_db(self.conn,self.client,self.cursor):
            u=None

        
        if when and when < 80:
            tick=curtick+when
            eta=when
        elif when and when < curtick:
            self.client.reply(prefix,nick,target,"Can not unbook targets in the past. You wanted tick %s, but current tick is %s."%(when,curtick))
            return 1
        elif when:
            tick=when
            eta=tick-curtick

        if not override: # trying to unbook own target
            query="DELETE FROM target WHERE pid = %s " 
            args=(p.id,)
            if when:
                query+=" AND tick = %s "
                args+=(tick,)
            else:
                query+=" AND tick > %s "
                args+=(curtick,)
            if u:
                #query+=" AND (uid ILIKE %s OR uid IS NULL)"
                query+=" AND uid ILIKE %s"
                args+=(u.id,)
            else:
                query+=" AND nick ILIKE %s"
                args+=(nick,)

            self.cursor.execute(query,args)
            if self.cursor.rowcount == 0:
                reply="You have no bookings matching %s:%s:%s" %(p.x,p.y,p.z)
                if when:
                    reply+=" for landing on tick %s"%(tick,)
                reply+=". If you are trying to unbook someone else's target, you must confirm with 'yes'."
            else:
                reply="You have unbooked %s:%s:%s"%(p.x,p.y,p.z)
                if when:
                    reply+=" for landing pt %s"%(tick,)
                else:
                    reply+=" for %d booking(s)"%(self.cursor.rowcount)
                reply+="."

        else:
            query="SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid, t2.pnick AS pnick, t2.userlevel AS userlevel "
            query+=" FROM target AS t1 LEFT JOIN user_list AS t2 ON t1.uid=t2.id "
            query+=" WHERE t1.pid=%s "
            args=(p.id,)
            if when:
                query+=" AND tick=%s"
                args+=(tick,)
            else:
                query+=" AND tick > %s"
                args+=(curtick,)
            self.cursor.execute(query,args)
            if self.cursor.rowcount < 1:
                reply="No bookings matching %s:%s:%s" %(p.x,p.y,p.z)
                if when:
                    reply+=" for landing on tick %s"%(tick,)
                self.client.reply(prefix,nick,target,reply)
                return 1
                                  
            res=self.cursor.dictfetchall()
            
            query="DELETE FROM target WHERE pid = %s "
            args=(p.id,)
            if when:
                query+=" AND tick = %s "
                args+=(tick,)
            else:
                query+=" AND tick > %s "
                args+=(curtick,)
                
            self.cursor.execute(query,args)
            
            reply="You have unbooked %s:%s:%s"%(p.x,p.y,p.z)
            if when:
                owner=res[0]['nick']
                type="nick"
                if res[0]['pnick']:
                    owner=res[0]['pnick']
                    type="user"
                reply+=" for landing pt %s (previously held by %s %s)"%(res[0]['tick'],type,owner)
            else:
                reply+=" for %d booking(s): "%(self.cursor.rowcount)
                prev=[]
                for r in res:
                    owner="nick: "+r['nick']
                    if r['pnick']:
                        owner="user: "+r['pnick']
                    prev.append("(%s %s)" % (r['tick'],owner))
                reply+=" "+string.join(prev,', ')
                
        self.client.reply(prefix,nick,target,reply)
        return 1
    
