"""
Loadable.Loadable subclass
"""
class slogan(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^\s+(.*)$")
        self.usage=self.__class__.__name__ + ""

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        m=self.paramre.search(m.group(1))
        params=None
        if m:
            params=m.group(1)

        
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        args=()
        query="SELECT slogan FROM slogan WHERE 1=1"

        if params:
            query+=" AND slogan ILIKE %s"
            args+=("%"+params+"%",)

        query+=" ORDER BY RANDOM()"
        self.cursor.execute(query,args)

        reply=""
        if self.cursor.rowcount == 0:
            reply+="No slogans matching '%s'" % (params,)
        else:
            res=self.cursor.dictfetchone()
            reply+="%s" %(res['slogan'],)
            if self.cursor.rowcount > 1 and params:
                reply+=" (%d more slogans match this search)" % (self.cursor.rowcount - 1)
                
        self.client.reply(prefix,nick,target,reply)
        

        # do stuff here
        
        return 1
    
