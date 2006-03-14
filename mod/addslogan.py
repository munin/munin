"""
Loadable.Loadable subclass
"""
class addslogan(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^\s+(.*)$")
        self.usage=self.__class__.__name__ + " <slogan goes here>"

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

        args=(params,)
        query="INSERT INTO slogan (slogan) VALUES (%s)"

        self.cursor.execute(query,args)

        reply="Added your shitty slogan"    
        
                
        self.client.reply(prefix,nick,target,reply)
        

        # do stuff here
        
        return 1
    
