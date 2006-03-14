"""
Loadable subclass
"""

class maxcap(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^\s+(\d+)")
        self.usage=self.__class__.__name__ + " (<total roids>|<x:y:z>)"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        params=m.group(1)
        m=self.planet_coordre.search(params)
        if m:
            victim = loadable.planet(x=m.group(1),y=m.group(2),z=m.group(3))
            if not victim.load_most_recent(self.conn,self.client,self.cursor):
                self.client.reply(prefix,nick,target,"%s:%s:%s is not a valid planet" % (victim.x,victim.y,victim.z))
                return 1
            total_roids=victim.size
        else:
            m=self.paramre.search(params)
            if not m:
                self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
                return 0
            
            total_roids=int(m.group(1))
        
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        reply=""
        cap=0
        for i in range(1,7):
            cap+=total_roids/4
            reply+="Wave %d: %d (%d), " % (i,total_roids/4,cap)
            total_roids = total_roids - total_roids/4
        self.client.reply(prefix,nick,target,reply.strip(', '))

        return 1
