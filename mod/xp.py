"""
Loadable.Loadable subclass
"""

class xp(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^\s+(.*)")
        #self.firstcountre=re.compile(r"^(\d+)\s+(.*)")
        self.countre=re.compile(r"^(\d+)(\.|-|:|\s*)(.*)")        
        self.usage=self.__class__.__name__ + " [roids] <x:y:z> <a:b:c>"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        params=m.group(1)

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        roid_count = -1

        victim = None
        attacker = None
        
        #m=self.countre.search(params)
        #if m and not ':.-'.rfind(m.group(2))>-1:
        #    roid_count=int(m.group(1))
        #    params=m.group(3)

        m=self.planet_coordre.search(params)
        if m:
            victim = loadable.planet(x=m.group(1),y=m.group(2),z=m.group(3))
            if not victim.load_most_recent(self.conn,self.client,self.cursor):
                self.client.reply(prefix,nick,target,"%s:%s:%s is not a valid planet" % (victim.x,victim.y,victim.z))
                return 1
            params=params[m.end():]
                    
        m=self.planet_coordre.search(params)
        if m:
            attacker = loadable.planet(x=m.group(1),y=m.group(2),z=m.group(3))
            if not attacker.load_most_recent(self.conn,self.client,self.cursor):
                self.client.reply(prefix,nick,target,"%s:%s:%s is not a valid planet" % (attacker.x,attacker.y,attacker.z))
                return 1
            params=params[m.end():]
            
        if not victim:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 1

        if victim and not attacker:
            u=loadable.user(pnick=user)
            if not u.load_from_db(self.conn,self.client,self.cursor):
                self.client.reply(prefix,nick,target,"Usage: %s (you must be registered for automatic lookup)" % (self.usage,))
                return 1
            if u.planet_id:
                attacker = u.planet
            else:
                self.client.reply(prefix,nick,target,"Usage: %s (you must be registered for automatic lookup)" % (self.usage,))
                return 1

        if roid_count > -1:
            reply="Capturing %s roids " % (roid_count,)
            victim_val = victim.value
            victim_score = victim.score
            reply+="from %s:%s:%s (%s|%s) "%(victim.x,victim.y,victim.z,
                                          self.format_value(victim_val*100),self.format_value(victim_score*100))
            
            attacker_val = attacker.value
            attacker_score = attacker.score
            reply+="will earn %s:%s:%s (%s|%s) "%(attacker.x,attacker.y,attacker.z,
                                               self.format_value(attacker_val*100),self.format_value(attacker_score*100))

            bravery = min(20,5*(float(victim_val)/attacker_val)*(float(victim_score)/attacker_score))
            xp=int(bravery*roid_count)
            reply+="XP: %s, Score: %s (Bravery: %.2f)" % (xp,xp*50,bravery)
            self.client.reply(prefix,nick,target,reply)
        else:
            reply="Target "
            victim_val = victim.value
            attacker_val = attacker.value
            victim_score = victim.score
            attacker_score = attacker.score
            
            reply+="%s:%s:%s (%s|%s) "%(victim.x,victim.y,victim.z,
                                     self.format_value(victim_val*100),self.format_value(victim_score*100))
            reply+="| Attacker %s:%s:%s (%s|%s) "%(attacker.x,attacker.y,attacker.z,
                                                self.format_value(attacker_val*100),self.format_value(attacker_score*100))
            total_roids = victim.size

            #bravery = min(20,10*(float(victim_val)/attacker_val))
            bravery = min(20,5*(float(victim_val)/attacker_val)*(float(victim_score)/attacker_score))
                        
            reply+="| Bravery: %.2f " % (bravery,)
            
            cap=total_roids/4
            xp=int(cap*bravery)
            reply+="| Roids: %s | XP: %s | Score: %s" % (cap,xp,xp*50)
            self.client.reply(prefix,nick,target,reply)
        
                
        return 1
