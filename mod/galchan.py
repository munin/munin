"""
Loadable subclass
"""

class galchan(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^\s+(#\S+)")
        self.usage=self.__class__.__name__ + " <chan> "
        self.helptext=["This command adds Munin to the designated channel as a galchannel. The access of commands is limited to 1 in that channel (so you don't accidentally do !intel or something 'important'. You must make sure to add Munin to the channel _before_ you perform this command. If you fuck up and add the wrong channel, fuck you because then an HC has to manually remove it for you."]
    
    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to add galchannels")
            return 0
        
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        
        chan=m.group(1).lower()
        
        
        
        query="INSERT INTO channel_list (chan,userlevel,maxlevel) VALUES (%s,1,1)"
        
        try:
            self.cursor.execute(query,(chan,))
            if self.cursor.rowcount>0:
                #self.client.reply(prefix,nick,target,"Added chan %s at level %s" % (chan,access_lvl))
                self.client.reply(prefix,nick,target,"Added your galchannel as %s (if you didn't add me to the channel with at least access 24 first, I'm never going to bother joining)" % (chan,))
                self.client.privmsg('P',"set %s autoinvite on" %(chan,));
                self.client.privmsg('P',"invite %s" %(chan,));
                
        except psycopg.IntegrityError:
            self.client.reply(prefix,nick,target,"Channel %s already exists" % (chan,))
            return 0
        except:
            raise

        return 1
