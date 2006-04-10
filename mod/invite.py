"""
Loadable.Loadable subclass
"""

class invite(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + " <gimp>"

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
        gimp=m.group(1)

        query="SELECT * FROM invite(%s,%s)"# AS t1(success BOOLEAN, retmessage TEXT)"
        self.cursor.execute(query,(user,gimp))
        
        res=self.cursor.dictfetchone()
        
        if res['success']:
            # msg p adduser
            # msg p modinfo automode
            self.client.privmsg('P',"adduser #ascendancy %s 399" %(gimp,));
            self.client.privmsg('P',"modinfo #ascendancy automode %s op" %(gimp,));
            reply="You have successfully invited '%s'. The gimp is now your responsibility. If they fuck up and didn't know, it's your fault. So teach them well." % (gimp,)
            #reply="You have sponsored '%s'. In 36 hours you may use the !invite command to make them a member. It is your responsibility to get feedback about their suitability as a member in this period" % (gimp,)
        else:
            reply="You may not invite '%s'. Reason: %s"%(gimp,res['retmessage'])
        self.client.reply(prefix,nick,target,reply)
                                                                    

        # do stuff here

        return 1
