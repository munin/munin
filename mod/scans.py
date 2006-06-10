"""
Loadable.Loadable subclass
"""

class scans(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + " <x:y:z>"
	self.helptext=None

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0
        
        m=self.planet_coordre.search(m.group(1))
        if  m:
           
            x=m.group(1)
            y=m.group(2)
            z=m.group(3)
            
            p=loadable.planet(x=x,y=y,z=z)
            if not p.load_most_recent(self.conn,self.client,self.cursor):
                self.client.reply(prefix,nick,target,"No planet matching '%s:%s:%s' found"%(x,y,z))
                return 1
            
            query="SELECT scantype,max(tick) AS latest,count(*) AS count FROM scan WHERE pid=%s GROUP BY scantype"
            self.cursor.execute(query,(p.id,))
            
            reply=""
            if self.cursor.rowcount < 1:
                reply+="No scans available on %s:%s:%s" % (p.x,p.y,p.z)
                
            else:
                reply+="scans for %s:%s:%s -" % (p.x,p.y,p.z)
                prev=[]
                for p in self.cursor.dictfetchall():
                    prev.append("(%d %s, latest pt%s)" % (p['count'],p['scantype'],p['latest']))
                    
                reply+=" "+string.join(prev,', ')
            
                
            self.client.reply(prefix,nick,target,reply)

        else:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        return 1
