"""
Loadable.Loadable subclass
"""

#desc: send smses to members
#type: defbot
#example: !sms newt get online you faggot

class sms(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,200)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)\s+(.*)")
        self.usage=self.__class__.__name__ + " <nick> <message>"
	self.helptext=['username auto-added to the end of each sms.']

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        nick2 = m.group(1)
        self.cursor.execute("SELECT phone,pubphone from user_list where pnick=%s",(nick,))
        row = self.cursor.fetchone()
        if not row:
            self.client.reply(prefix,nick,target,"user %s does not exist!" % (nick2,))
            return 1

        if row[1] == 0:
            self.client.reply(prefix,nick,target,"%s's phone number is private... not sending." % (nick2,))
            return 1

        if len(row[0]) <= 6:
            self.client.reply(prefix,nick,target,"%s has an incorrect phone number - %s - not sending" % (nick2,row[0]))
            return 1

        phone = row[0]
        text = m.group(2) + ' - %s' % user
        if len(text) >= 160:
            self.client.reply(prefix,nick,target,"Max length for a text is 160 characters - your\'s was %i long." % (len(text),))
            return 1

        username = self.config.get("clickatell", "user")
        password = self.config.get("clickatell", "pass")
        api_id = self.config.get("clickatell", "api")

        from clickatell import Clickatell
        import md5

        ct = Clickatell(username, password, api_id)

        if not ct.auth():
            self.client.reply(prefix,nick,target,"sms NOT sent - could not authenticate with the server")
            return 1

        hasher = md5.new()
        hasher.update(phone)
        hasher.update(text)
        msg_id = hasher.hexdigest()
    
        message = {
            'to': str(phone),
            'text': str(text),
            'climsgid': str(msg_id)
        }
    
        res, msg = ct.sendmsg(message)
        if not res:
            self.client.reply(prefix,nick,target,"Failed to send a message '%s' to %s: %s!" % (text, phone, msg))
            return 1

        self.client.reply(prefix,nick,target,"Sent message '%s' to %s" % (text, user))

        return 1

