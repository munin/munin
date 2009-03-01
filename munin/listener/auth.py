import re

class auth(object):
    def __init__(self,client,config):
        self.client = client
        self.config = config
        self.welcomre=re.compile(r"\S+\s+(001|433).*",re.I)
        self.pinvitere=re.compile(r"^:P!cservice@netgamers.org\s+INVITE\s+\S+\s+:#(\S+)",re.I)
    def message(self,line):
        m=self.welcomre.search(line)
        if m:
            if self.config.has_option("IRC","auth"):
                self.client.wline("PRIVMSG P@cservice.netgamers.org :recover %s %s " % (self.config.get('Connection','nick'),self.config.get("IRC", "auth")))
                self.client.wline("PRIVMSG P@cservice.netgamers.org :auth %s" % (self.config.get("IRC", "auth")))
            if self.config.has_option("IRC", "modes"): self.client.wline("MODE %s +%s" % (self.config.get("Connection",'nick'), self.config.get("IRC", "modes")))
            return
        m=self.pinvitere.search(line)
        if m:
            self.client.wline("JOIN #%s" % m.group(1))
            return

