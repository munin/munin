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

class sms(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,conn,cursor):
        loadable.loadable.__init__(self,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)\s+(.*)")
        self.usage=self.__class__.__name__ + " <nick> <message>"
	self.helptext=['Sends an SMS to the specified user. Your username will be appended to the end of each sms. The user must have their phone correctly added and you must have access to their number.']

    def execute(self,nick,username,host,target,prefix,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        
        u=self.load_user(user,prefix,nick,target)
        if not u: return 1

        rec = m.group(1)
        text = m.group(2) + ' - %s' % user
        receiver=self.load_user_from_pnick(rec)
        if not receiver:
            irc_msg.reply("No user matching %s does not exist!" % (reciever,))
            return 1

        results=self.phone_query_builder(nick,username,host,target,prefix,command,receiver,access,"AND t1.friend_id=%s",(u.id,))

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

        hasher = md5.new()
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

        irc_msg.reply("Successfully processed To: %s Message: %s" % (receiver.pnick,text))
        return 0

    def prepare_phone_number(self,text):
        if not text:
            return text
        s = "".join([c for c in text if c.isdigit()])
        return s.lstrip("00")