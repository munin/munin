"""
Loadable subclass
"""

# This file is part of Munin.

# Munin is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# Munin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Munin; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen 
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright 
# owners.

# No alliance specific things found in this module.
# qebab, 24/6/08.

class lookup(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + " [<[x:y[:z]]|[alliancename]>]"

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0
            

        m=self.paramre.search(m.group(1))
        if not m or not m.group(1):
            u=loadable.user(pnick=user)
            if not u.load_from_db(self.conn,self.client,self.cursor):
                self.client.reply(prefix,nick,target,"You must be registered to use the automatic "+self.__class__.__name__+" command (log in with P and set mode +x, then make sure you've set your planet with the pref command)")        
                #self.client.reply(prefix,nick,target,"Usage: %s (you must be registered for automatic lookup)" % (self.usage,))
                return 1
            if u.planet:
                self.client.reply(prefix,nick,target,str(u.planet))
            else:
                self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 1
        param=m.group(1)
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
                self.client.reply(prefix,nick,target,str(p))
                return 1
            else:
                g=loadable.galaxy(x=x,y=y)
                if not g.load_most_recent(self.conn,self.client,self.cursor):
                    self.client.reply(prefix,nick,target,"No galaxy matching '%s' found"%(param,))
                    return 1
                self.client.reply(prefix,nick,target,str(g))  
                return 1

        #check if this is an alliance
        a=loadable.alliance(name=param.strip())
        if not a.load_most_recent(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"No alliance matching '%s' found" % (param,))
            return 1
        self.client.reply(prefix,nick,target,str(a))
        
        # do stuff here

        return 1
