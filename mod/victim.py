"""
Loadable.Loadable subclass
"""

class victim(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile("\s+(.*)")
#        re.compile(r"(\s+(\S+))?(\s+(ter|cat|xan|zik))(\s+(<|>)?(\d+))?(\s+(<|>)?(\d+))?",re.I)
        self.alliancere=re.compile(r"(\S+)")
        self.racere=re.compile(r"^(ter|cat|xan|zik)$",re.I)
        self.rangere=re.compile(r"(<|>)?(\d+)")
        self.usage=self.__class__.__name__ + " [alliance] [race] [<|>][size] [<|>][value]" + " (must include at least one search criteria, order doesn't matter except that size *must* precede value)"
        
    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        
        # assign param variables
        
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0
        alliance=None
        race=None
        size_mod=None
        size=None
        value_mod=None
        value=None

        param=m.group(1)
        params=param.split()

        for p in params:
            m=self.racere.search(p)
            if m and not race:
                race=m.group(1)
                continue
            m=self.rangere.search(p)
            if m and not size and int(m.group(2)) < 32768:
                size_mod=m.group(1) or '>' 
                size=m.group(2)
                continue
            m=self.rangere.search(p)
            if m and not value:
                value_mod=m.group(1) or '<'
                value=m.group(2)
                continue
            m=self.alliancere.search(p)
            if m and not alliance:
                alliance=m.group(1) 
                continue




        
        victims=self.victim(alliance,race,size_mod,size,value_mod,value)
        i=0
        if not len(victims):
            reply="No"
            if race:
                reply+=" %s"%(race,)
            reply+=" planets"
            if alliance:
                reply+=" in intel matching alliance: %s,"%(alliance,)
            else:
                reply+=" matching"
            if size:
                reply+=" size %s %s" % (size_mod,size)
            if value:
                reply+=" value %s %s" % (value_mod,value)
            self.client.reply(prefix,nick,target,reply)
        for v in victims:
            reply="%s:%s:%s (%s)" % (v['x'],v['y'],v['z'],v['race'])
            reply+=" Value: %s Size: %s" % (v['value'],v['size'])
            if v['nick']:
                reply+=" Nick: %s" % (v['nick'],)
            if not alliance and v['alliance']:
                reply+=" Alliance: %s" % (v['alliance'],)
            i+=1
            if i>4 and len(victims)>4:
                reply+=" (Too many victims to list, please refine your search)"
                self.client.reply(prefix,nick,target,reply)
                break
            self.client.reply(prefix,nick,target,reply)
        
        
        return 1
    
    def victim(self,alliance='ascendancy',race=None,size_mod='>',size=None,value_mod='<',value=None):
        args=()
        query="SELECT t1.x AS x,t1.y AS y,t1.z AS z,t1.size AS size,t1.size_rank AS size_rank,t1.value AS value,t1.value_rank AS value_rank,t1.race AS race,t2.alliance AS alliance,t2.nick AS nick"
        query+=" FROM planet_dump AS t1 INNER JOIN planet_canon AS t3 ON t1.id=t3.id"
        query+=" INNER JOIN intel AS t2 ON t3.id=t2.pid"
        query+=" WHERE t1.tick=(SELECT MAX(tick) FROM updates)"

        if alliance:
            query+=" AND t2.alliance ILIKE %s"
            args+=('%'+alliance+'%',)
        if race:
            query+=" AND race ILIKE %s"
            args+=(race,)
        if size:
            query+=" AND size %s " % (size_mod) + "%s"
            args+=(size,)
        if value:
            query+=" AND value %s " % (value_mod) + "%s"
            args+=(value,)
        query+=" ORDER BY t1.size DESC, t1.value DESC"
        self.cursor.execute(query,args)
        return self.cursor.dictfetchall()

