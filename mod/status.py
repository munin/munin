"""
Loadable.Loadable subclass
"""

class status(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^(\s+(.*))?")
        self.coordre=re.compile(r"^(\d+)[ .:-](\d+)([ .:-](\d+))?([ .:-](\d+))?")
        self.nickre=re.compile(r"^(\D\S*)?(\s*(\d+))?$")
        self.usage=self.__class__.__name__ + " [<nick|user>|<x:y[:z]>] [tick]"
        
    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        # assign param variables
        param=m.group(2)
        if not param: param=""

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0
        curtick=self.current_tick()
        m=self.coordre.search(param)
        if m:
            x=m.group(1)
            y=m.group(2)
            z=m.group(4)
            when=m.group(6)
            if when:
                when=int(when)
            if when and when < 80:
                tick=curtick+when
                eta=when
            elif when and when < curtick:
                self.client.reply(prefix,nick,target,"Can not check status on the past. You wanted tick %s, but current tick is %s. (If you really need to know, poke jester.)"%(when,curtick))
                return 1
            elif when:
                tick=when
                eta=tick-curtick
                                                                                            
            args=()
            query="SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid, t2.pnick AS pnick, t2.userlevel AS userlevel, t3.x AS x, t3.y AS y, t3.z AS z"
            query+=" FROM target AS t1"
            query+=" INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
            query+=" LEFT JOIN user_list AS t2 ON t1.uid=t2.id"
            query+=" WHERE"
            
            if when:
                query+=" t1.tick = %s"
                args+=(tick,)
            else:
                query+=" t1.tick > (SELECT MAX(tick) FROM updates)"
            query+=" AND t3.tick = (SELECT MAX(tick) FROM updates) AND t3.x=%s AND t3.y=%s"

            if z:
                p=loadable.planet(x=x,y=y,z=z)
                if not p.load_most_recent(self.conn,self.client,self.cursor):
                    self.client.reply(prefix,nick,target,"No planet matching '%s:%s:%s' found"%(x,y,z))
                    return 1                    
                query+=" AND t3.z=%s"
                            
                self.cursor.execute(query,args+(x,y,z))
                if self.cursor.rowcount < 1:
                    reply="No bookings matching planet %s:%s:%s"%(x,y,z)
                    if when:
                        reply+=" for tick %s"%(tick,)
                    self.client.reply(prefix,nick,target,reply)
                    return 1
                reply="Status for %s:%s:%s -" % (x,y,z)
                if when:
                    res=self.cursor.dictfetchall()
                    type="nick"
                    owner=res[0]['nick']
                    if res[0]['pnick']:
                        owner=res[0]['pnick']
                        type="user"
                    reply+=" booked for landing pt %s (eta %s) by %s %s"%(res[0]['tick'],res[0]['tick']-curtick,type,owner)
                        
                else:
                    prev=[]
                    for r in self.cursor.dictfetchall():
                        owner="nick:"+r['nick']
                        if r['pnick']:
                            owner="user:"+r['pnick']
                        prev.append("(%s %s)" % (r['tick'],owner))

                    reply+=" "+string.join(prev,', ')
                self.client.reply(prefix,nick,target,reply)
            else:
                query+=" ORDER BY y, z, x, tick"
                
                self.cursor.execute(query,args+(x,y))
                
                if self.cursor.rowcount < 1:
                    reply="No bookings matching galaxy %s:%s"%(x,y)
                    if when:
                        reply+=" for tick %s"%(tick,)
                    self.client.reply(prefix,nick,target,reply)
                    return 1
                ticks={}
                for r in self.cursor.dictfetchall():
                    if not ticks.has_key(r['tick']):
                        ticks[r['tick']]=[]
                    ticks[r['tick']].append(r)

                reply="Target information for %s:%s (by landing tick) -" % (x,y)
                sorted_keys=ticks.keys()
                sorted_keys.sort()
                for k in sorted_keys:
                    reply=string.join([reply,"Tick %s (eta %s)" % (k,k-curtick)])
                    booked_list=ticks[k]
                    prev=[]
                    for p in booked_list:
                        owner="nick:"+p['nick']
                        if p['pnick']:
                            owner="user:"+p['pnick']
                        prev.append("(%s %s)" % (p['z'],owner))
                            
                        
                    reply+=" "+string.join(prev,', ')
                    self.client.reply(prefix,nick,target,reply.strip())
                    reply=""
            return 1
        
        m=self.nickre.search(param)
        if m:
            subject=m.group(1)
            when=m.group(3)
            if when: when=int(when)
            if subject: subject=subject.strip()
            
            if when and when < 80:
                tick=curtick+when
                eta=when
            elif when and when < curtick:
                self.client.reply(prefix,nick,target,"Can not check status on the past. You wanted tick %s, but current tick is %s. (If you really need to know, poke jester.)"%(when,curtick))
                return 1
            elif when:
                tick=when
                eta=tick-curtick

            if not subject:
                if user:
                    subject=user
                else:
                    subject=nick
                    
            args=()
            query="SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid, t2.pnick AS pnick, t2.userlevel AS userlevel, t3.x AS x, t3.y AS y, t3.z AS z"
            query+=" FROM target AS t1"
            query+=" INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
            query+=" LEFT JOIN user_list AS t2 ON t1.uid=t2.id"
            query+=" WHERE"
            
            if when:
                query+=" t1.tick = %s"
                args+=(tick,)
            else:
                query+=" t1.tick > (SELECT MAX(tick) FROM updates)"
                
            query+=" AND t3.tick = (SELECT MAX(tick) FROM updates) AND (t1.nick ILIKE %s OR t2.pnick ILIKE %s)"
            self.cursor.execute(query,args+('%'+subject+'%','%'+subject+'%'))
            if self.cursor.rowcount < 1:
                reply="No active bookings matching nick/user %s" %(subject)
                self.client.reply(prefix,nick,target,reply)
                return 1
            reply="Bookings matching nick/user %s"%(subject)
            if when:
                reply+=" for landing on tick %s (eta %s):"%(tick,tick-curtick)
                prev=[]
                for b in self.cursor.dictfetchall():
                    tmp="(%s:%s:%s as "%(b['x'],b['y'],b['z'])
                    if b['pnick']:
                        tmp+="user: %s" %(b['pnick'])
                    else:
                        tmp+="nick: %s" %(b['nick'])
                    tmp+=")"
                    prev.append(tmp)

                reply+=" "+string.join(prev,', ')
                
            else:
                prev=[]
                for b in self.cursor.dictfetchall():
                    tmp="(%s:%s:%s landing pt%s/eta %s"%(b['x'],b['y'],b['z'],b['tick'],b['tick']-curtick)
                    if b['pnick']:
                        tmp+=" user:%s" %(b['pnick'])
                    else:
                        tmp+=" nick:%s" %(b['nick'])
                    tmp+=")"
                    prev.append(tmp)
                reply+=" "+string.join(prev,', ')
            self.client.reply(prefix,nick,target,reply)
            
        return 1



