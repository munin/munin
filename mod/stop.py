"""
Loadable.Loadable subclass
"""

class stop(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^\s+(\d+)\s+(\S+)")
        self.usage=self.__class__.__name__ + " <number> <ship to stop>"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        ship_number=int(m.group(1))
        bogey=m.group(2).lower()
        
        
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

