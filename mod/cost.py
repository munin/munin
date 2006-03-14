"""
Loadable subclass
"""

class cost(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^\s+(\d+)\s+(\S+)")
        self.usage=self.__class__.__name__ + " <number> <shipname>"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        ship_number=int(m.group(1))
        ship_name=m.group(2)
                
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        query="SELECT * FROM ship WHERE name ILIKE %s"

        self.cursor.execute(query,("%"+ship_name+"%",))
        ship=self.cursor.dictfetchone()
        if not ship:
            self.client.reply(prefix,nick,target,"%s is not a ship" % (ship_name))
            return 0

        self.client.reply(prefix,nick,target,"Buying %s %s will cost %s metal, %s crystal and %s eonium. It will add %s value" %(ship_number,ship['name'],
                                                                                                                                 ship['metal'] * ship_number,
                                                                                                                                 ship['crystal'] * ship_number,
                                                                                                                                 ship['eonium'] * ship_number,
                                                                                                                                 (ship['total_cost'] * ship_number)/100))
        
        return 1
        
"""        
        if not ship:
            if "asteroids".rfind(bogey) > -1:
                self.client.reply(prefix,nick,target,"Buying %s %s will cost %s metal, %s crystal and %s eonium. It will add %s value" %(ship_number,ship['name'],
                                                                                                                                         ship['metal'] * ship_number,
                                                                                                                                         ship['crystal'] * ship_number,
                                                                                                                                         ship['eonium'] * ship_number,
                                                                                                                                         (ship['total_cost'] * ship_number)/100))
                
                ship={'name':'Asteroid','class':'Roids','armor':50,'total_cost':20000}
            elif "structures".rfind(bogey) > -1:
                
                ship={'name':'Structure','class':'Struct','armor':500,'total_cost':150000}
            else:
                self.client.reply(prefix,nick,target,"%s is not a ship" % (bogey))
                return 0
"""                
