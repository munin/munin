"""
Loadable.Loadable subclass
"""

class stop(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^\s+(\d+[mk]?)\s+(\S+)")
        self.usage=self.__class__.__name__ + " <number> <ship to stop>"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        params=m.group(1)
        m=self.paramre.search(params)
        if not m:
            if re.search("\s+hammertime",params,re.I):
                self.client.reply(prefix,nick,target,"Can't touch this!")
                return 1
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        ship_number=m.group(1)

        if ship_number[-1].lower()=='k':
            ship_number=1000*int(ship_number[:-1])
        elif ship_number[-1].lower()=='m':
            ship_number=1000000*int(ship_number[:-1])
        else:
            ship_number=int(ship_number)        

        bogey=m.group(2)        
        
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        query="SELECT * FROM ship WHERE name ILIKE %s"
                
        self.cursor.execute(query,("%"+bogey+"%",))
        ship=self.cursor.dictfetchone()
        if not ship:
            if "asteroids".rfind(bogey) > -1:
                ship={'name':'Asteroid','class':'Roids','armor':50,'total_cost':20000}
            elif "structures".rfind(bogey) > -1:
                ship={'name':'Structure','class':'Struct','armor':500,'total_cost':150000}
            else:
                self.client.reply(prefix,nick,target,"%s is not a ship" % (bogey))
                return 0
        total_armor=ship['armor']*ship_number

        # do stuff here
        query="SELECT * FROM ship WHERE target=%s"
        self.cursor.execute(query,(ship['class'],))
        attackers=self.cursor.dictfetchall()
        
        reply=""
        if ship['class'].lower() == "roids":
            reply+="Capturing "
        elif ship['class'].lower() == "struct":
            reply+="Destroying "
        else:
            reply+="Stopping "
        reply+="%s %s (%s) requires " % (ship_number,ship['name'],self.format_value(ship_number*ship['total_cost']))

        for a in attackers:
            needed=total_armor/a['damage']
            reply+="%s: %s (%s) " % (a['name'],needed,self.format_value(a['total_cost']*needed))
        self.client.reply(prefix,nick,target,reply.strip())
            
        return 1

