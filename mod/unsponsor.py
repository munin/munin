"""
Loadable.Loadable subclass
"""

class unsponsor(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + "<pnick>"
        
    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0
        if not user:
            self.client.reply(prefix,nick,target,"You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
        
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        
        # assign param variables
        recruit=m.group(1)
        
        # do stuff here

        query="SELECT * FROM unsponsor(%s,%s)"# AS t1(success BOOLEAN, retmessage TEXT)"
        self.cursor.execute(query,(user,recruit))

        res=self.cursor.dictfetchone()
 
        if res['success']:
            reply="You have unsponsored '%s'. " % (recruit,)
        else:
            reply="You may not unsponsor '%s'. Reason: %s"%(recruit,res['retmessage'])
        self.client.reply(prefix,nick,target,reply)
        
        return 1
                                                                                                                                            
