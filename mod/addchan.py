"""
Loadable subclass
"""

class addchan(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,500)
        self.paramre=re.compile(r"^\s+(#\S+)\s+(\d+)")
    
    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: addchan <chan> <level>")
            return 0
        
        chan=m.group(1).lower()
        access_lvl=int(m.group(2))

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to add new channels")
            return 0
        
        if access_lvl >= access:
            self.client.reply(prefix,nick,target,"You may not add a channel with equal or higher access to your own")
            return 0
        
        query="INSERT INTO channel_list (chan,userlevel) VALUES (%s,%s)"
        
        try:
            self.cursor.execute(query,(chan,access_lvl))
            if self.cursor.rowcount>0:
                self.client.reply(prefix,nick,target,"Added chan %s at level %s" % (chan,access_lvl))
        except psycopg.IntegrityError:
            self.client.reply(prefix,nick,target,"Channel %s already exists" % (chan,))
            return 0
        except:
            raise

        return 1
