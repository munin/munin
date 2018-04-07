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

CRLF = "\r\n"
DEBUG = 1


class connection:
    "Client wrapper class for IRC server command line interface"
    NOTICE_PREFIX = 1
    PUBLIC_PREFIX = 2
    PRIVATE_PREFIX = 3

    def __init__(self, config, command):
        "Connect to an IRC hub"
        self.config = config
        self.command = command

    def connect(self):
        "do nowt"

    def wline(self, line):
        "Send a line to the hub"
        print(line)

    def rline(self):
        if self.command:
            command = ":dummy!~un@%s.users.netgamers.org PRIVMSG Munin :.%s" % (self.config.get("Auth","owner_pnick"),self.command)
            self.command = None
            return command
        else:
            return None
        return "PRIVMSG jester: %s" % (command,)

    def privmsg(self, target, text):
        self.wline("PRIVMSG %s :%s" % (target, text))
        pass

    def notice(self, target, text):
        self.wline("NOTICE %s :%s" % (target, text))
        pass

    def reply(self, prefix, nick, target, text):
        if prefix == self.NOTICE_PREFIX:
            self.wline("NOTICE %s :%s" % (nick, text))
        if prefix == self.PUBLIC_PREFIX:
            m = re.match(r"(#\S+)", target, re.I)
            if m:
                self.wline("PRIVMSG %s :%s" % (target, text))
            else:
                prefix = self.PRIVATE_PREFIX
        if prefix == self.PRIVATE_PREFIX:
            self.wline("PRIVMSG %s :%s" % (nick, text))
