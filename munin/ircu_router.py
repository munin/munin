class ircu_router:
    def __init__(self,client,config,reboot):
        self.client=client
        self.config=config
        self.reboot=reboot


    def run(self):
        self.client.wline("NICK %s" % config.get("Connection", "nick"))
        self.client.wline("USER %s 0 * : %s" % (config.get("Connection", "user"),
                                                config.get("Connection", "name")))

        while 1:
            line = self.client.rline()
            if not line:
                break
            self.handler.parse(line)

    def parse(self,line):
        self.trigger_listeners(line)
        self.run_command(line)

    def run_command(self,line):
        irc_msg = irc_message.irc_message(client = self.client,
                                          line   = line)
        m=self.privmsgre.search(line);
        if m:
            irc_msg=irc_message.irc_message(client   = self.client,
                                            nick     = m.group(1),
                                            username = m.group(2),
                                            host     = m.group(3),
                                            target   = m.group(4),
                                            message  = m.group(5),
                                            prefix   = m.group(6),
                                            command  = m.group(7))

            user=self.getpnick(host)
            m=self.commandre.search(message)
            if not m:
                return None
            prefix=m.group(1)
            command=m.group(2)


    def trigger_listeners(self):
        for r in listeners.keys():
            if r.search(line):
                listeners.message(line)

