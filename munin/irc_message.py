# This file is part of Munin.

# Munin is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# Munin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Munin; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

import re


class irc_message(object):
    def __init__(
        self,
        client=None,
        cursor=None,
        line=None,
        nick=None,
        username=None,
        host=None,
        target=None,
        message=None,
        prefix=None,
        command=None,
        config=None,
    ):
        self.notprefix = r"~|-|\."
        self.pubprefix = r"!"
        self.privprefix = "@"
        self.privmsgre = re.compile(
            r"^:(\S+)!(\S+)@(\S+)\s+PRIVMSG\s+(\S+)\s+:(\s*(%s|%s|%s)(.*?)\s*)$"
            % (self.notprefix, self.pubprefix, self.privprefix)
        )
        self.bifrost_privmsgre = re.compile(
            r"^:bifrost!\S+@bifrost.users.netgamers.org\s+PRIVMSG\s+(\S+)\s+:<(\S+)>(\s*(%s|%s|%s)(.*?)\s*)$"
            % (self.notprefix, self.pubprefix, self.privprefix)
        )
        self.pnickre = re.compile(r"(\S{2,15})\.users\.netgamers\.org")
        self.client = client
        self.cursor = cursor
        self.command = None
        self.round = config.getint("Planetarion", "current_round")

        m = self.bifrost_privmsgre.search(line)
        if m:
            self.nick = m.group(2)
            self.username = "bifrost"
            self.host = m.group(2) + ".users.netgamers.org"
            self.target = m.group(1)
            self.message = m.group(3)
            self.prefix = "!"
            self.command = m.group(5)
        else:
            m = self.privmsgre.search(line)
            if m:
                self.nick = m.group(1)
                self.username = m.group(2)
                self.host = m.group(3)
                self.target = m.group(4)
                self.message = m.group(5)
                self.prefix = m.group(6)
                self.command = m.group(7)

        if self.command:
            com_parts = self.command.split(" ", 1)
            self.command_name = com_parts[0]
            self.command_parameters = None
            self.user = self.getpnick(self.host)
            self.access = self.getaccess(self.user, self.target)
            if len(com_parts) > 1:
                self.command_parameters = com_parts[1]
                # !round <number> <command> [params]...
                if self.command_name == "round" or self.command_name == "r":
                    com_parts = self.command.split(" ", 3)
                    if len(com_parts) > 2:
                        try:
                            self.round = int(com_parts[1])
                            self.command_name = com_parts[2]
                            if len(com_parts) > 3:
                                self.command_parameters = com_parts[3]
                                self.command = "%s %s" % (com_parts[2], com_parts[3])
                            else:
                                self.command_parameters = ""
                                self.command = self.command_name

                        except ValueError as s:
                            self.reply("Invalid round number %s given" % (com_parts[1]))
            # print "Round: %s, Command: %s, Parameters: %s"%(self.round,self.command_name,self.command_parameters)

    def reply(self, message):
        self.client.reply(prefix, nick, target, message)

    def prefix_numeric(self):
        if self.notprefix.replace("|", "").find(self.prefix) > -1:
            return self.client.NOTICE_PREFIX
        if self.pubprefix.replace("|", "").find(self.prefix) > -1:
            return self.client.PUBLIC_PREFIX
        if self.privprefix.replace("|", "").find(self.prefix) > -1:
            return self.client.PRIVATE_PREFIX
        return -1

    def prefix_notice(self):
        return self.notprefix.replace("|", "").find(self.prefix) > -1

    def prefix_private(self):
        return self.privprefix.replace("|", "").find(self.prefix) > -1

    def reply(self, text):
        if self.command.isupper():
            text = text.upper()
        self.client.reply(self.prefix_numeric(), self.nick, self.target, text)

    def user_or_nick(self):
        return self.user or self.nick

    def chan_reply(self):
        m = re.match(r"(#\S+)", self.target, re.I)
        if m and self.prefix_numeric() == self.client.PUBLIC_PREFIX:
            return True
        else:
            return False

    def getpnick(self, host):
        m = self.pnickre.search(host)
        if m:
            return m.group(1)
        else:
            return None

    def get_userlevel(self, user):
        query = "SELECT userlevel FROM user_list WHERE pnick ilike %s"
        self.cursor.execute(query, (user,))
        if self.cursor.rowcount > 0:
            return int(self.cursor.fetchone()["userlevel"])
        else:
            return 0

    def get_chanlevel(self, target, userlevel):
        query = "SELECT userlevel, maxlevel FROM channel_list WHERE chan ilike %s"
        self.cursor.execute(query, (target,))
        chanlevel = 0
        maxlevel = userlevel
        if self.cursor.rowcount > 0:
            res = self.cursor.fetchone()
            chanlevel = int(res["userlevel"])
            maxlevel = int(res["maxlevel"])
        return (chanlevel, maxlevel)

    def getaccess(self, user, target):
        userlevel = self.get_userlevel(user)
        (chanlevel, maxlevel) = self.get_chanlevel(target, userlevel)
        access = max(userlevel, chanlevel)
        if self.prefix_notice() or self.prefix_private():
            return access
        else:
            return min(access, maxlevel)
