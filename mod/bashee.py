"""
Loadable.Loadable subclass
"""

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08

class bashee(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
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
        planet = None
        param = m.group(1)
        m=self.paramre.search(param)

        if not m or not m.group(1):
            u=loadable.user(pnick=user)
            if not u.load_from_db(self.conn,self.client,self.cursor):
                self.client.reply(prefix,nick,target,"You must be registered to use the automatic "+self.__class__.__name__+" command (log in with P and set mode +x, then make sure you've set your planet with the pref command)")
                #
                return 1
            if u.planet:
                planet = u.planet
            else:
                self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
                return 1
        else:
            m=self.coordre.search(param)
            if m:
                x=m.group(1)
                y=m.group(2)
                z=m.group(4)
                # assign param variables
                if z:
                    p=loadable.planet(x=x,y=y,z=z)
                    if not p.load_most_recent(self.conn,self.client,self.cursor):
                        self.client.reply(prefix,nick,target,"No planet matching '%s' found"%(param,))
                        return 1
                    planet = p
            else:
                self.client.reply(prefix,nick,target,"Usage: %s (you must be registered for automatic lookup)" % (self.usage,))
                return 1
        if planet:
            reply="%s:%s:%s can be hit by planets with value %d or below or score %d or below"%(planet.x,planet.y,planet.z,int(planet.value*2.5),int(planet.score*5/3))

        self.client.reply(prefix,nick,target,reply)
        return 1
