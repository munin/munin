"""
Loadable.Loadable subclass
"""

class pref(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + " [option=value]+"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        u=loadable.user(pnick=user)
        if not u.load_from_db(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"You must be registered to use the pref command")
            return 1


        param_dict=self.split_opts(m.group(1))
        if param_dict == None:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 1

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        for opt in param_dict:
            val=param_dict[opt]
            if opt == "planet":
                m=self.planet_coordre.search(val)
                if m:
                    x=m.group(1)
                    y=m.group(2)
                    z=m.group(3)
                else:
                    self.client.reply(prefix,nick,target,"You must provide coordinates (x:y:z) for the planet option")
                    continue
                self.save_planet(prefix,nick,target,u,x,y,z)
            if opt == "stay":
                self.save_stay(prefix,nick,target,u,val,access)
                

        return 1

    def save_planet(self,prefix,nick,target,u,x,y,z):
        p=loadable.planet(x=x,y=y,z=z)
        if not p.load_most_recent(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"%s:%s:%s is not a valid planet" % (x,y,z))
            return 0

        if u.planet_id > 0:
            query="UPDATE user_pref SET planet_id=%s WHERE id=%s"
            self.cursor.execute(query,(p.id,u.id))
            self.client.reply(prefix,nick,target,"Your planet has been saved as %s:%s:%s" % (x,y,z))
        else:
            query="INSERT INTO user_pref (id,planet_id) VALUES (%s,%s)"
            self.cursor.execute(query,(u.id,p.id))
            self.client.reply(prefix,nick,target,"Your planet has been saved as %s:%s:%s" % (x,y,z))
        
    def save_stay(self,prefix,nick,target,u,status,access):
        if access < 100:
            return 0
        print "Trying to set stay to %s"%(status,)
        query=""
        args=()
        if u.pref:
            query="UPDATE user_pref SET stay=%s WHERE id=%s"
            args+=(status,u.id)
        else:
            query="INSERT INTO user_pref (id,stay) VALUES (%s,%s)"
            args+=(u.id,status)
        reply="Your stay status has been saved as %s"%(status,)
        try:
            self.cursor.execute(query,args)
        except psycopg.ProgrammingError :
            reply="Your stay status '%s' is not a valid value. If you are staying for next round, it should be 'yes'. Otherwise it should be 'no'." %(status,)
        self.client.reply(prefix,nick,target,reply)

            
