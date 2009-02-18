import irc_message

class ircu_router:
    def __init__(self,client,config,reboot):
        self.client=client
        self.config=config
        self.reboot=reboot
        self.listeners={}

    def run(self):
        while 1:
            line = self.client.rline()
            if not line:
                break
            self.parse(line)

    def parse(self,line):
        self.trigger_listeners(line)
        self.run_command(line)

    def run_command(self,line):
         irc_msg = irc_message.irc_message(client = self.client,
                                           line   = line)


    def trigger_listeners(self,line):
        for r in self.listeners.keys():
            if r.search(line):
                self.listeners[r].message(line)

