import munin.irc_message as irc_message

from munin.reboot import reboot


class command(object):
    def __init__(self, client, cursor, module, loader, config):
        self.client = client
        self.cursor = cursor
        self.module = module
        self.config = config
        self.control = self.register_control(module, loader)

    def register_control(self, module, loader):
        modules = loader.get_submodules(module.__name__)
        result = {}
        for m in modules:
            modname = m.__name__.split(".")[-1]
            if not hasattr(m, modname):
                print(
                    "Warning: Unable to find '%s' in module %s" % (modname, m.__name__)
                )
            else:
                result[m.__name__] = getattr(m, modname)(self.cursor)
        return result

    def message(self, line):
        irc_msg = irc_message.irc_message(
            client=self.client, cursor=self.cursor, config=self.config, line=line
        )
        if irc_msg.command:
            key = "munin.mod." + irc_msg.command_name.lower()
            try:
                if key in self.control:
                    self.control[key].execute(irc_msg.user, irc_msg.access, irc_msg)
                    self.log_command(irc_msg)
                elif key == "munin.mod.help":
                    self.help(irc_msg)
                else:
                    for c in self.control.values():
                        if c.aliases(irc_msg.command_name.lower()):
                            c.execute(irc_msg.user, irc_msg.access, irc_msg)
                            self.log_command(irc_msg)
                            break
            except reboot:
                raise
            except Exception as e:
                irc_msg.reply(
                    "Error in module '%s'. Please report the command you used to the bot owner as soon as possible."
                    % (irc_msg.command_name,)
                )
                raise

    def log_command(self, irc_msg):
        if irc_msg.command.lower() == "pref":
            return
        query = "INSERT INTO command_log (command_prefix,command,command_parameters,nick,pnick,username,hostname,target)"
        query += " VALUES"
        query += " (%s,%s,%s,%s,%s,%s,%s,%s)"

        self.cursor.execute(
            query,
            (
                irc_msg.prefix,
                irc_msg.command_name,
                irc_msg.command_parameters,
                irc_msg.nick,
                irc_msg.user,
                irc_msg.username,
                irc_msg.host,
                irc_msg.target,
            ),
        )

    def help(self, irc_msg):
        if len(irc_msg.command_parameters) > 0:
            key = "munin.mod." + irc_msg.command_parameters
            if key in self.control:
                self.control[key].help(irc_msg.user, irc_msg.access, irc_msg)
            else:
                irc_msg.reply("No command matching '%s'" % irc_msg.command_parameters)
        else:
            irc_msg.reply(
                "Munin help. For more information use: <"
                + irc_msg.notprefix.replace("|", "")
                + irc_msg.pubprefix.replace("|", "")
                + irc_msg.privprefix.replace("|", "")
                + ">help <command>. Built-in commands: help"
            )

            command_list = sorted(
                [
                    x.__class__.__name__
                    for x in [
                        x
                        for x in list(self.control.values())
                        if irc_msg.access >= x.level
                    ]
                ]
            )
            command_list = ", ".join(command_list)
            irc_msg.reply(command_list)
        pass
