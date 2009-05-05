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

import re
import munin.loadable as loadable

class smslog(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s*(\d+)?")
        self.usage=self.__class__.__name__ + " [id]"
	self.helptext=['Show the last ten SMS sent, or the text of a specific SMS sender.']

    def execute(self,user,access,irc_msg):
        m=self.commandre.search(irc_msg.command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        id=m.group(1)

        if id:
            self.show_sms(id,irc_msg)
        else:
            self.show_all(irc_msg)

        return 1

    def show_sms(self,id,irc_msg):
        query=self.base_query()
        query+=" WHERE t1.id=%s"
        self.cursor.execute(query,(id,))
        if self.cursor.rowcount < 1:
            irc_msg.reply("There was no SMS sent with ID %s"%(id,))
        else:
            r=self.cursor.dictfetchone()
            reply="SMS with ID %s sent by %s to %s with text: %s"%(r['id'],r['sender'],r['receiver'],r['sms_text'])
            irc_msg.reply(reply)
            
    def show_all(self,irc_msg):
        query=self.base_query()
        query+=" ORDER BY t1.id DESC LIMIT 10"
        self.cursor.execute(query)
        res=self.cursor.dictfetchall()
        reply="Last 10 SMSes: "
        reply+=", ".join(map(lambda x: "id: %s (%s -> %s)"%(x['id'],x['sender'],x['receiver']),res))
        irc_msg.reply(reply)

    def base_query(self):
        query="SELECT t1.id AS id, t2.pnick AS sender, t3.pnick AS receiver"
        query+=", t1.sms_text AS sms_text"
        query+=" FROM sms_log AS t1"
        query+=" INNER JOIN user_list AS t2"
        query+=" ON t1.sender_id = t2.id"
        query+=" INNER JOIN user_list AS t3"
        query+=" ON t1.receiver_id = t3.id"
        return query        
