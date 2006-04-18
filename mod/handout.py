"""
Loadable.Loadable subclass
"""

class handout(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,500)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\d+)(\s+(\S+))?")
        self.usage=self.__class__.__name__ + ""

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0


        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0
        
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        # assign param variables 
        num_invites=int(m.group(1))
        to_nick=m.group(3)

        reply=""
        if to_nick:
            query="UPDATE user_list SET invites = invites + %d WHERE userlevel >= 100 AND pnick=%s"
            self.cursor.execute(query,(num_invites,to_nick))
            if self.cursor.rowcount < 1:
                reply+="Could not find any users with userlevel 100 or higher matching pnick '%s'" % (to_nick,)
            else:
                reply+="Added %d invites to user '%s'" %(num_invites,to_nick)
        else:
            query="UPDATE user_list SET invites = invites + %d WHERE userlevel >= 100" %(num_invites,)
            self.cursor.execute(query,(num_invites,to_nick))
            reply+="Added %d invites to all users with userlevel 100 or higher" %(num_invites,)

        self.client.reply(prefix,nick,target,reply)

        return 1
