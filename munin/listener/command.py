import munin.irc_message as irc_message
import os

class command(object):
    def __init__(self,client,cursor,module,loader,reboot):
        self.client=client
        self.cursor=cursor
        self.module=module
        self.reboot=reboot
        self.control=self.register_control(module,loader)

    def register_control(self,module,loader):
        modules=loader.get_submodules(module.__name__)
        result={}
        for m in modules:
            result[m.__name__]=getattr(m,m.__name__.split('.')[-1])(self.cursor)
        return result


    def message(self,line):
        irc_msg = irc_message.irc_message(client = self.client,
                                          cursor = self.cursor,
                                          line   = line)
        if irc_msg.command:
            key = "munin.mod."+irc_msg.command.split()[0]
            if self.control.has_key(key):
                self.control[key].execute(irc_msg.user,irc_msg.access,irc_msg)
                self.log_command(irc_msg)
            elif key == 'munin.mod.reboot' and irc_msg.access >= 1000:
                self.reboot()


    def log_command(self,irc_msg):
        if irc_msg.command.lower() == 'pref':
            return
        query="INSERT INTO command_log (command_prefix,command,command_parameters,nick,pnick,username,hostname,target)"
        query+=" VALUES"
        query+=" (%s,%s,%s,%s,%s,%s,%s,%s)"
        command_list = irc_msg.command.split(' ',1)
        command_command = command_list[0]
        command_parameters = None
        if len(command_list) > 1:
            command_parameters = command_list[1]

        self.cursor.execute(query,(irc_msg.prefix,
                                   command_command,
                                   command_parameters,
                                   irc_msg.nick,
                                   irc_msg.user,
                                   irc_msg.username,
                                   irc_msg.host,
                                   irc_msg.target))

