import irc_message
from listener import command
import mod

class ircu_router:
    def __init__(self,client,cursor,config,loader,reboot):
        self.client=client
        self.cursor=cursor
        self.config=config
        self.reboot=reboot
        self.listeners=[
            command.command(client,cursor,mod,loader)
            ]

    def run(self):
        while 1:
            line = self.client.rline()
            if not line:
                break
            self.trigger_listeners(line)

    def trigger_listeners(self,line):
        for l in self.listeners:
            l.message(line)
