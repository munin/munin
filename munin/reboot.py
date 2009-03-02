
class reboot(Exception):
    def __init__(self,irc_msg):
        self.irc_msg=irc_msg
        pass
    def __str__(self):
        "Reboot"
