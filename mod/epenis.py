"""
Loadable.Loadable subclass
"""

class epenis(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^(\s+(\S+))?")
        self.usage=self.__class__.__name__ + ""
        
    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        search=user or nick
        m=self.paramre.search(m.group(1))

        if m:
            search=m.group(2) or search


        query="DROP TABLE epenis;DROP SEQUENCE xp_gain_rank;DROP SEQUENCE value_diff_rank;DROP SEQUENCE activity_rank;"
        try:
            self.cursor.execute(query)
        except:
            pass

        query="CREATE TEMP SEQUENCE xp_gain_rank;CREATE TEMP SEQUENCE value_diff_rank;CREATE TEMP SEQUENCE activity_rank"
        self.cursor.execute(query)
        query="SELECT setval('xp_gain_rank',1,false); SELECT setval('value_diff_rank',1,false); SELECT setval('activity_rank',1,false)"
        self.cursor.execute(query)

            
        query="CREATE TABLE epenis AS"
        query+=" (SELECT *,nextval('activity_rank') AS activity_rank"
        query+=" FROM (SELECT  *,nextval('value_diff_rank') AS value_diff_rank"
        query+=" FROM (SELECT *,nextval('xp_gain_rank') AS xp_gain_rank"
        query+=" FROM (SELECT t2.nick, t4.pnick ,t1.xp-t5.xp AS xp_gain, t1.score-t5.score AS activity, t1.value-t5.value AS value_diff"
        query+=" FROM planet_dump AS t1"
        query+=" INNER JOIN intel AS t2 ON t1.id=t2.pid"
#        query+=" LEFT JOIN user_pref AS t3 ON t2.pid=t3.planet_id"
        query+=" LEFT JOIN user_list AS t4 ON t2.pid=t4.planet_id"
        query+=" INNER JOIN planet_dump AS t5"
        query+=" ON t1.id=t5.id AND t1.tick - 72 = t5.tick"
        query+=" WHERE t1.tick = (select max(tick) from updates)"
        query+=" AND t2.alliance ILIKE '%asc%'"
        query+=" ORDER BY xp_gain DESC) AS t6"
        query+=" ORDER BY value_diff DESC) AS t7"
        query+=" ORDER BY activity DESC) AS t8)"

        self.cursor.execute(query)

        query="SELECT nick,pnick,xp_gain,activity,value_diff,xp_gain_rank,value_diff_rank,activity_rank"
        query+=" FROM epenis"
        query+=" WHERE pnick ILIKE %s"

        self.cursor.execute(query,('%'+search+'%',))
        if self.cursor.rowcount < 1:
            query="SELECT nick,pnick,xp_gain,activity,value_diff,xp_gain_rank,value_diff_rank,activity_rank"
            query+=" FROM epenis"
            query+=" WHERE nick ILIKE %s"
            
            self.cursor.execute(query,('%'+search+'%',))

        res=self.cursor.dictfetchone()
        if not res:
            reply="No epenis stats matching %s"% (search,)
        else:
            person=res['pnick'] or res['nick']
            reply ="epenis for %s is %s score long. This makes %s rank: %s for epenis in Ascendancy!" % (person,res['activity'],person,res['activity_rank'])

        self.client.reply(prefix,nick,target,reply)
        
        return 1

                                                                                                                                            
