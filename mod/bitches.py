"""
Loadable.Loadable subclass
"""

class bitches(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^\s+(\d+)")
        self.usage=self.__class__.__name__ + " [minimum eta]"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0
        
        # do stuff here
        args=()
        query="SELECT t3.x AS x, t3.y AS y, count(*) AS number"
        query+=" FROM target AS t1"
        query+=" INNER JOIN planet_dump AS t3 ON t1.pid=t3.id"
        query+=" LEFT JOIN user_list AS t2 ON t1.uid=t2.id"

        m=self.paramre.search(m.group(1))
        if m:
            query+=" WHERE t1.tick >= ((SELECT MAX(tick) FROM updates)+%s)"
            args+=(m.group(1),)
        else:
            query+=" WHERE t1.tick > (SELECT MAX(tick) FROM updates)"
        query+="  AND t3.tick = (SELECT MAX(tick) FROM updates)"
        query+=" GROUP BY x, y ORDER BY x, y"


            

        self.cursor.execute(query,args)
        if self.cursor.rowcount < 1:
            reply="No active bookings. This makes Munin sad. Please don't make Munin sad."
            self.client.reply(prefix,nick,target,reply)
            return 1
        reply="Active bookings:"
        prev=[]
        for b in self.cursor.dictfetchall():
            prev.append("%s:%s(%s)"%(b['x'],b['y'],b['number']))

        reply+=" "+string.join(prev,', ')
        self.client.reply(prefix,nick,target,reply)
        return 1
