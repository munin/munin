"""
Loadable.Loadable subclass
"""

class ascinfo(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^\s+(STUFFGOESHERE)")
        self.usage=self.__class__.__name__ + ""
        
    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        # assign param variables
        
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        query="SELECT count(*) AS members,sum(t1.value) AS tot_value, sum(t1.score) AS tot_score, sum(t1.size) AS tot_size, sum(t1.xp) AS tot_xp"
        query+=" FROM planet_dump AS t1"
        query+=" INNER JOIN intel AS t2 ON t1.id=t2.pid"
        query+=" WHERE t1.tick=(SELECT MAX(tick) FROM updates) AND t2.alliance ILIKE '%asc%'"

        self.cursor.execute(query)

        res=self.cursor.dictfetchone()
        
        reply="Ascendancy Members: %s, Value: %s, Avg: %s," % (res['members'],res['tot_value'],res['tot_value']/res['members'])
        reply+=" Score: %s, Avg: %s," % (res['tot_score'],res['tot_score']/res['members']) 
        reply+=" Size: %s, Avg: %s, XP: %s, Avg: %s" % (res['tot_size'],res['tot_size']/res['members'],res['tot_xp'],res['tot_xp']/res['members'])
        self.client.reply(prefix,nick,target,reply)
        
        return 1
                                                                                                                                            
