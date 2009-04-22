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

import re
from hashlib import md5
from munin import loadable
from clickatell import Clickatell


class sms(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)\s+(.*)")
        self.usage=self.__class__.__name__ + " <nick> <message>"
	self.helptext=['Sends an SMS to the specified user. Your username will be appended to the end of each sms. The user must have their phone correctly added and you must have access to their number.']

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        u=self.load_user(user,irc_msg)
        if not u: return 1

        rec = m.group(1)
        public_text = m.group(2) + ' - %s' % (user,)
        text = public_text + '/%s' %(u.phone,)
        receiver=self.load_user_from_pnick(rec)
        if not receiver:
            irc_msg.reply("Who exactly is %s?" % (rec,))
            return 1
        if receiver.pnick.lower() == 'valle':
            irc_msg.reply("I refuse to talk to that Swedish clown. Use !phone show Valle and send it using your own phone.")
            return 

        results=self.phone_query_builder(receiver,"AND t1.friend_id=%s",(u.id,))

        if not (receiver.pubphone or len(results)>0):
            irc_msg.reply("%s's phone number is private or they have not chosen to share their number with you. Supersecret message not sent." % (receiver.pnick,))
            return 1

        phone = self.prepare_phone_number(receiver.phone)
        if not phone or len(phone) <= 6:
            irc_msg.reply("%s has no phone number or their phone number is too short to be valid (under 6 digits). Super secret message not sent." % (receiver.pnick,))
            return 1

        if len(text) >= 160:
            irc_msg.reply("Max length for a text is 160 characters. Your text was %i characters long. Super secret message not sent." % (len(text),))
            return 1

        username = self.config.get("clickatell", "user")
        password = self.config.get("clickatell", "pass")
        api_id = self.config.get("clickatell", "api")

        ct = Clickatell(username, password, api_id)

        if not ct.auth():
            irc_msg.reply("Could not authenticate with server. Super secret message not sent.")
            return 1

        hasher = md5()
        hasher.update(phone)
        hasher.update(text)
        msg_id = hasher.hexdigest()

        message = {
            'to': str(phone),
            'sender': "Munin",
            'text': str(text),
            'climsgid': str(msg_id),
            'msg_type': 'SMS_TEXT'
        }

        ret = ct.sendmsg(message)
        if not ret[0]:
            irc_msg.reply("That wasn't supposed to happen. I don't really know what wrong. Maybe your mother dropped you.")
            return 1
        reply="Successfully processed To: %s Message: %s"
        if irc_msg.chan_reply():
            irc_msg.reply(reply % (receiver.pnick,public_text))
        else:
            irc_msg.reply(reply % (receiver.pnick,text))
        self.log_message(u.id,receiver.id,phone, public_text)
        return 0

    def prepare_phone_number(self,text):
        if not text:
            return text
        s = "".join([c for c in text if c.isdigit()])
        return s.lstrip("00")

    def log_message(self,sender_id,receiver_id,phone,text):
        query="INSERT INTO sms_log (sender_id,receiver_id,phone,sms_text)"
        query+=" VALUES (%s,%s,%s,%s)"
        self.cursor.execute(query,(sender_id,receiver_id,phone,text))
                            
