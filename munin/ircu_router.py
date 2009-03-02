from listener import auth
from listener import command
from listener import custom_runner
import mod

class ircu_router(object):
    def __init__(self,client,cursor,config,loader):


        self.client=client
        self.cursor=cursor
        self.config=config
        self.listeners=[
            command.command(client,cursor,mod,loader),
            custom_runner.custom_runner(client,cursor,config),
            auth.auth(client,config)
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
