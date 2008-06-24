"""
Loadable.Loadable subclass
"""

# This module doesn't have anything ascendancy specific in it.
# qebab, 24/6/08.

class quits(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + " <nick>"
        self.helptext=None
        
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
        quit=m.group(1)

        
        # do stuff here
        query="SELECT pnick, quit FROM user_list WHERE pnick ILIKE %s"
        self.cursor.execute(query,('%'+quit+'%',))

        reply=""

        if self.cursor.rowcount == 0:
            reply="'%s' does not match any users" % (quit,) 
        else:
            r=self.cursor.dictfetchone()
            pnick=r['pnick']
            count=r['quit']
            self.cursor.execute(query,(pnick,))
            if count<=0:
                reply="%s is a stalwart defender of his honor" % (pnick,)
            else:
                reply="%s is a whining loser who has quit %d times." % (pnick,count)
        self.client.reply(prefix,nick,target,reply)
        

        return 1
    
                                                                                                                                                          
