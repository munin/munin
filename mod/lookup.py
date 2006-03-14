"""
Loadable subclass
"""

class lookup(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + " [<[x:y[:z]]|[alliancename]>]"

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
                self.client.reply(prefix,nick,target,u.planet)
            else:
                self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 1
        param=m.group(1)
        m=self.coordre.search(param)
        if m:
            x=m.group(1)
            y=m.group(2)
            z=m.group(4)
            # assign param variables 
            
            if z:
                p=loadable.planet(x=x,y=y,z=z)
                if not p.load_most_recent(self.conn,self.client,self.cursor):
                    self.client.reply(prefix,nick,target,"No planet matching '%s' found"%(param,))
                    return 1
                self.client.reply(prefix,nick,target,p)
                return 1
            else:
                g=loadable.galaxy(x=x,y=y)
                if not g.load_most_recent(self.conn,self.client,self.cursor):
                    self.client.reply(prefix,nick,target,"No galaxy matching '%s' found"%(param,))
                    return 1
                self.client.reply(prefix,nick,target,g)  
                return 1

        #check if this is an alliance
        a=loadable.alliance(name=param.strip())
        if not a.load_most_recent(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"No alliance matching '%s' found" % (param,))
            return 1
        self.client.reply(prefix,nick,target,a)
        
        # do stuff here

        return 1
