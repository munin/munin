import munin.irc_message as irc_message
import os

class command:
    def __init__(self,client,cursor,module,loader):
        self.client=client
        self.cursor=client
        self.module=module
        self.control=self.register_control(module,loader)

    def register_control(self,module,loader):
        print "registering %s"%(module.__name__,)
        modules=loader.get_submodules(module.__name__)
        result={}
        for m in modules:
            print m.__name__
            result[m.__name__]=getattr(m,m.__name__.split('.')[-1])(self.cursor)
        return result


    def message(self,line):
         irc_msg = irc_message.irc_message(client = self.client,
                                           cursor = self.cursor,
                                           line   = line)
         if irc_msg.command:
             print "irc_msg found command %s" % (irc_msg.command,)

