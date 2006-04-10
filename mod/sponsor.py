"""
Loadable.Loadable subclass
"""

class sponsor(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)(\s+(.*))")
        self.usage=self.__class__.__name__ + " <pnick> [comments]"
        
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
        comment=m.group(3)
        
        # do stuff here

        query="SELECT * FROM sponsor(%s,%s,%s)"# AS t1(success BOOLEAN, retmessage TEXT)"
        self.cursor.execute(query,(user,recruit,comment))

        res=self.cursor.dictfetchone()
 
        if res['success']:
            reply="You have sponsored '%s' (MAKE SURE THIS IS THE RECRUIT'S P-LOGIN.) In 36 hours you may use the !invite command to make them a member. It is your responsibility to get feedback about their suitability as a member in this period" % (recruit,)
        else:
            reply="You may not sponsor '%s'. Reason: %s"%(recruit,res['retmessage'])
        self.client.reply(prefix,nick,target,reply)
        
        return 1
                                                                                                                                            
