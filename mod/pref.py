"""
Loadable.Loadable subclass
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

# This module doesn't have anything alliance specific as far as I can tell.
# qebab, 24/6/08.

class pref(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + " [option=value]+"
        self.helptext=['Options: planet=x.y.z | password=OnlyWorksInPM | phone=+1-800-HOT-BIRD | pubphone=T|F']
    def execute(self,nick,username,host,target,prefix,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        u=loadable.user(pnick=user)
        if not u.load_from_db(self.conn,irc_msg.client,self.cursor):
            irc_msg.reply("You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
            #irc_msg.reply("You must be registered to use the pref command")
            return 1


        param_dict=self.split_opts(m.group(1))
        if param_dict == None:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 1

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
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
                    irc_msg.reply("You must provide coordinates (x:y:z) for the planet option")
                    continue
                pid = self.save_planet(prefix,nick,target,u,x,y,z)
                if pid > 0 and u.userlevel >= 100:
                    a=loadable.alliance(name=self.config.get('Auth', 'alliance'))
                    if a.load_most_recent(self.conn,irc_msg.client,self.cursor):
                        i=loadable.intel(pid=pid)
                        i.load_from_db(self.conn,irc_msg.client,self.cursor)
                        if i.id:
                            query="UPDATE intel SET "
                            query+="nick=%s,alliance_id=%s"
                            query+=" WHERE id=%s"
                            self.cursor.execute(query,(user,a.id,i.id))
                        else:
                            query="INSERT INTO intel (pid,nick,alliance_id) VALUES (%s,%s,%s)"
                            self.cursor.execute(query,(pid,user,a.id))
            if opt == "stay":
                self.save_stay(prefix,nick,target,u,val,access)
            if opt == "pubphone":
                self.save_pubphone(prefix,nick,target,u,val,access)
            if opt == "password":
                self.save_password(prefix,nick,target,u,val)
                pass
            if opt == "phone":
                self.save_phone(prefix,nick,target,u,val)
                pass

        return 1

    def save_planet(self,prefix,nick,target,u,x,y,z):
        p=loadable.planet(x=x,y=y,z=z)
        if not p.load_most_recent(self.conn,irc_msg.client,self.cursor):
            irc_msg.reply("%s:%s:%s is not a valid planet" % (x,y,z))
            return 0

        if u.pref:
            query="UPDATE user_list SET planet_id=%s WHERE id=%s"
            self.cursor.execute(query,(p.id,u.id))
            irc_msg.reply("Your planet has been saved as %s:%s:%s" % (x,y,z))
            return p.id
        else:
            raise Exception("This code /should/ be defunct now that prefs are in the user_list table")
            query="INSERT INTO user_pref (id,planet_id) VALUES (%s,%s)"
            self.cursor.execute(query,(u.id,p.id))
            irc_msg.reply("Your planet has been saved as %s:%s:%s" % (x,y,z))

    def save_stay(self,prefix,nick,target,u,status,access):
        if access < 100:
            return 0
        print "Trying to set stay to %s"%(status,)
        query=""
        args=()
        if u.pref:
            query="UPDATE user_list SET stay=%s WHERE id=%s"
            args+=(status,u.id)
        else:
            raise Exception("This code /should/ be defunct now that prefs are in the user_list table")
            query="INSERT INTO user_pref (id,stay) VALUES (%s,%s)"
            args+=(u.id,status)
        reply="Your stay status has been saved as %s"%(status,)
        try:
            self.cursor.execute(query,args)
        except psycopg.ProgrammingError :
            reply="Your stay status '%s' is not a valid value. If you are staying for next round, it should be 'yes'. Otherwise it should be 'no'." %(status,)
        irc_msg.reply(reply)

    def save_phone(self,prefix,nick,target,u,passwd):
        print "trying to set phone for %s"%(u.pnick,)
        query="UPDATE user_list SET phone = %s"
        query+=" WHERE id = %s"

        self.cursor.execute(query,(passwd,u.id))
        if self.cursor.rowcount > 0:
            irc_msg.reply( "Updated your phone number. Remember to set your phone to public (!pref pubphone=yes) or allow some people to see your phone number (!phone allow stalker) or no one will be able to see your number.")
        else:
            irc_msg.reply( "Something went wrong. Go whine to your sponsor.")

    def save_pubphone(self,prefix,nick,target,u,status,access):
        if access < 100:
            irc_msg.reply(
                              "Only %s members can allow all members of %s to view their phone"%(self.config.get('Auth','alliance'),
                                                                                                 self.config.get('Auth','alliance')))
            return 0
        query=""
        args=()
        query="UPDATE user_list SET pubphone=%s WHERE id=%s"
        args+=(status,u.id)
        reply="Your pubphone status has been saved as %s"%(status,)
        try:
            self.cursor.execute(query,args)
        except psycopg.ProgrammingError :
            reply="Your pubphone status '%s' is not a valid value. If you want your phone number to be visible to all %s members, it should be 'yes'. Otherwise it should be 'no'." %(status,self.config.get('Auth','alliance'))
        irc_msg.reply(reply)
    def save_password(self,prefix,nick,target,u,passwd):
        print "trying to set password for %s"%(u.pnick,)
        query="UPDATE user_list SET passwd = MD5(MD5(salt) || MD5(%s))"
        query+=" WHERE id = %s"

        m=re.match(r"(#\S+)",target,re.I)
        if m:
            irc_msg.reply("Don't set your password in public you shit")
        else:
            self.cursor.execute(query,(passwd,u.id))
            if self.cursor.rowcount > 0:
                irc_msg.reply( "Updated your password")
            else:
                irc_msg.reply( "Something went wrong. Go whine to your sponsor.")
