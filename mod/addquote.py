"""
Loadable.Loadable subclass
"""

class addquote(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^\s+(.*)$")
        self.timestampre=re.compile(r"\s*\[?\s*\d+:\d+(:\d+)?\s*\]?\s*")
        self.usage=self.__class__.__name__ + " <quote goes here>"

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

        params=self.striptimestamps(params)
        args=(params,)

        query="INSERT INTO quote (quote) VALUES (%s)"
        self.cursor.execute(query,args)
        #reply="Added your shitty quote"    
        #self.client.reply(prefix,nick,target,reply)
        
        self.client.reply(prefix,nick,target,"Added your shitty quote: "+params)
        # do stuff here
        
        return 1
    
    def striptimestamps(self,s):
        """
        strip timestamps from s
        """
        s=self.timestampre.sub(' ',s)
        s=s.strip()
        return s
