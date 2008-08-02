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
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1000)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)(\s+(\S+))")
        self.usage=self.__class__.__name__ + " <allow|deny|show> <nick>"
	self.helptext=None

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        u=loadable.user(pnick=user)
        if not u.load_from_db(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")


        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        command=m.group(1)

        if "list".find(command) > 0:
            self.cursor.execute(query,(username.id,))
            results=self.cursor.dictfetchall()

            reply=""

            if self.cursor.rowcount < 1:
                reply="You have no friends. How sad. Maybe you should go post on http://grouphug.us or something."
            else:
                people=[]

                for b in self.cursor.dictfetchall():
                    people.append("%s"%(b['pnick'],))
                reply="The following people can view your phone number: "
                reply+=", ".join(people)

            self.client.reply(prefix,nick,target,reply)
            return 1


        trustee=m.group(2)
        t_user=loadable.user(pnick=trustee)
        if not u.load_from_db(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"%s is not a valid user."%(trustee,))
            return 0

        if "allow".find(command) > 0:
            results=self.phone_query_builder(nick,username,host,target,prefix,command,user,access,"AND t1.friend_id=%s",(t_user.id,))
            if len(results) > 0:
                reply="%s can already access your phone number."
            else:
                query="INSERT INTO phone (user_id,friend_id) VALUES (%s,%s)"
                args=(u.id,t_user.id)
                self.cursor.execute(query,args)
                reply="Added %s to the list of people able to view your phone number."%(t_user.pnick,)
            self.client.reply(prefix,nick,target, reply)
        elif "deny".find(command) > 0:
            query="DELETE FROM phone WHERE user_id=%s and friend_id=%s"
            args=(u.id,t_user.id)
            self.cursor.execute(query,args)

            reply=""
            if self.cursor.rowcount < 1:
                reply="Could not find %s among the people allowed to see your phone number."
            else:
                reply="Removed %s from the list of people allowed to see your phone number."
            self.client.reply(prefix,nick,target,reply)
        elif "show".find(command) > 0:
            results=self.phone_query_builder(nick,username,host,target,prefix,command,user,access,"AND t1.friend_id=%s",(u.id,))
            if len(results) < 1:
                reply="%s won't let you see their phone number. What a paranoid cunt."%(t_user.pnick,)
            else:
                reply="%s says his phone number is %s"%(t_user.pnick,t_user.phone)

            self.client.reply(prefix,nick,target,reply)


        # do stuff here

        return 1

    def phone_query_builder(self,nick,username,host,target,prefix,command,user,access,query_filter=None,query_args=None):
        args=(user.id,)
        query="SELECT pnick "
        query+=" FROM phone AS t1"
        query+=" INNER JOIN user_list AS t2"
        query+=" ON t2.id=t1.user_id"
        query+=" WHERE t1.user_id=%s"
        if query_filter:
            query+=query_filter
            args+=query_args

        self.cursor.execute(query,(query_args,))
