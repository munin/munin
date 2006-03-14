"""
Loadable subclass
"""

class raw(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1000)
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + ""

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        irc_command=m.group(1)

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to send raw ocmmands")
            return 0

        print "%s sent raw '%s'" % (user,irc_command)
        self.client.wline(irc_command)
        self.client.reply(prefix,nick,target,"Sent raw command '%s'" % (irc_command,))
                          
        return 1
