"""
Loadable subclass
"""

class remchan(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,500)
        self.paramre=re.compile(r"^\s+(#\S+)")
        self.usage=self.__class__.__name__ + " <channels>"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        
        chan=m.group(1).lower()         
        
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to remove channels")
            return 0
        
        
        query="SELECT chan,userlevel FROM channel_list WHERE chan=%s LIMIT 1"
        self.cursor.execute(query,(chan,))
        res=self.cursor.dictfetchone()
        if not res:
            self.client.reply(prefix,nick,target,"Channel '%s' does not exist" % (chan,))
            return 0
        access_lvl = res['userlevel']
        real_chan = res['chan']
        
        if access_lvl >= access:
            self.client.reply(prefix,nick,target,"You may not remove %s, the channel's access (%s) exceeds your own (%s)" % (chan, access_lvl, access))
            return 0
        
        query="DELETE FROM channel_list WHERE chan=%s"
        
        try:
            self.cursor.execute(query,(real_chan,))
            if self.cursor.rowcount>0:
                self.client.reply(prefix,nick,target,"Removed channel %s" % (real_chan,))
            else:
                self.client.reply(prefix,nick,target,"No channel removed" )
        except:
            raise
        
        return 1
        
            
