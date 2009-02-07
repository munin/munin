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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.



class phone(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,1)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)(\s+(\S+))?")
        self.usage=self.__class__.__name__ + " <list|allow|deny|show> <nick>"
	self.helptext=None

    def execute(self,nick,username,host,target,prefix,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        u=loadable.user(pnick=user)
        if not u.load_from_db(irc_msg.client,self.cursor):
            irc_msg.reply("You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        command=m.group(1)

        if "list".find(command) > -1:
            args=(u.id,)
            query="SELECT pnick "
            query+=" FROM phone AS t1"
            query+=" INNER JOIN user_list AS t2"
            query+=" ON t2.id=t1.friend_id"
            query+=" WHERE t1.user_id=%s"
            self.cursor.execute(query,args)
            results=self.cursor.dictfetchall()

            reply=""

            if len(results) < 1:
                reply="You have no friends. How sad. Maybe you should go post on http://grouphug.us or something."
            else:
                people=[]

                for b in results:
                    people.append(b['pnick'])
                reply="The following people can view your phone number: "
                reply+=", ".join(people)

            irc_msg.reply(reply)
            return 1


        trustee=m.group(3)
        t_user=loadable.user(pnick=trustee)

        if not t_user.load_from_db(irc_msg.client,self.cursor):
             irc_msg.reply("%s is not a valid user."%(trustee,))
             return 0

        if "allow".find(command) > -1:
            results=self.phone_query_builder(nick,username,host,target,prefix,command,u,access,"AND t1.friend_id=%s",(t_user.id,))
            if len(results) > 0:
                reply="%s can already access your phone number."%(t_user.pnick,)
            else:
                query="INSERT INTO phone (user_id,friend_id) VALUES (%s,%s)"
                args=(u.id,t_user.id)
                self.cursor.execute(query,args)
                reply="Added %s to the list of people able to view your phone number."%(t_user.pnick,)
            irc_msg.reply( reply)
            return 1
        elif "deny".find(command) > -1:
            query="DELETE FROM phone WHERE user_id=%s and friend_id=%s"
            args=(u.id,t_user.id)
            self.cursor.execute(query,args)

            reply=""
            if self.cursor.rowcount < 1:
                reply="Could not find %s among the people allowed to see your phone number." % (t_user.pnick,)
            else:
                reply="Removed %s from the list of people allowed to see your phone number." % (t_user.pnick,)
            irc_msg.reply(reply)
            return 1
        elif "show".find(command) > -1:
            if u.id == t_user.id:
                if u.phone:
                    reply="Your phone number is %s."%(u.phone,)
                    reply+=" Your pubphone setting is: %s"%(["off","on"][u.pubphone],)
                else:
                    reply="You haven't set your phone number. To set your phone number, do !pref phone=1-800-HOT-BIRD."
                irc_msg.reply(reply)
                return 1

            m=re.match(r"(#\S+)",target,re.I)
            if m and prefix==irc_msg.client.PUBLIC_PREFIX:
                irc_msg.reply("Don't look up phone numbers in public, Alki might see them")
                return 1
            if t_user.pubphone and u.userlevel >= 100:
                reply="%s says his phone number is %s"%(t_user.pnick,t_user.phone)
            else:
                results=self.phone_query_builder(nick,username,host,target,prefix,command,t_user,access,"AND t1.friend_id=%s",(u.id,))
                if len(results) < 1:
                    reply="%s won't let you see their phone number. That paranoid cunt just doesn't trust you I guess."%(t_user.pnick,)
                else:
                    if t_user.phone:
                        reply="%s says his phone number is %s"%(t_user.pnick,t_user.phone)
                    else:
                        reply="%s hasn't shared his phone number. What a paranoid cunt ."%(t_user.pnick,)

            irc_msg.reply(reply)
            return 1
        # if we're still here someone did something wrong
        irc_msg.reply("Usage: %s" % (self.usage,))

        return 1
