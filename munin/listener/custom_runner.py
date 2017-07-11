from munin.custom import scan
# from munin.custom import galstatus
import re


class custom_runner(object):
    def __init__(self, client, cursor, config):
        self.client = client
        self.cursor = cursor
        self.config = config
        # self.galstatus=galstatus.galstatus(self.client,self.cursor,self.config)
        self.scanre = re.compile("https?://[^/]+/showscan.pl\?scan_id=([0-9a-zA-Z]+)")
        self.scangrpre = re.compile("https?://[^/]+/showscan.pl\?scan_grp=([0-9a-zA-Z]+)")
        self.privmsgre = re.compile(r"^:(\S+)!(\S+)@(\S+)\s+PRIVMSG\s+(\S+)\s+:(.*)")
        self.pnickre = re.compile(r"(\S{2,15})\.users\.netgamers\.org")

    def message(self, line):
        m = self.privmsgre.search(line)
        if m:
            nick = m.group(1)
            target = m.group(4)
            message = m.group(5)
            user = self.getpnick(m.group(3))
            for m in self.scanre.finditer(message):
                self.scan(m.group(1), nick, user, None)
                pass
            for m in self.scangrpre.finditer(message):
                self.scan(None, nick, user, m.group(1))
                pass
            # self.galstatus.parse(message,nick,user,target)

    def scan(self, rand_id, nick, pnick, group_id):
        s = scan.scan(rand_id, self.client, self.config, nick, pnick, group_id)
        s.start()

    def getpnick(self, host):
        m = self.pnickre.search(host)
        if m:
            return m.group(1)
        else:
            return None
