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
import string
import random


class auth(object):
    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.welcomre = re.compile(r"\S+\s+(001)\s+(\S+).*", re.I)
        self.nicktakenre = re.compile(r"\S+\s+(433)\s+(\S+)\s+(\S+).*", re.I)
        self.pinvitere = re.compile(r"^:P!cservice@netgamers.org\s+INVITE\s+\S+\s+:?#(\S+)", re.I)
        self.desired_nick = config.get("Connection", "nick")

    def message(self, line):
        m = self.welcomre.search(line)
        if m:
            accepted_nick = m.group(2)
            if self.config.has_option("IRC", "modes"):
                self.client.wline("MODE %s +%s" % (accepted_nick, self.config.get("IRC", "modes")))
            if self.config.has_option("IRC", "auth"):
                self.client.wline("PRIVMSG P@cservice.netgamers.org :auth %s" % (self.config.get("IRC", "auth")))
            if accepted_nick != self.desired_nick and self.config.has_option("IRC", "auth"):
                self.client.wline("PRIVMSG P@cservice.netgamers.org :recover")
                self.client.wline("NICK %s" % self.desired_nick)
            return
        m = self.pinvitere.search(line)
        if m:
            self.client.wline("JOIN #%s" % m.group(1))
            return
        m = self.nicktakenre.search(line)
        if m:
            actual_nick = m.group(2)
            denied_nick = m.group(3)
            if actual_nick == '*':  # not registered with server yet; take a random nick, we'll deal with this later
                self.client.wline("NICK %s" % self.random_nick())
            elif denied_nick == self.desired_nick:  # just try harder
                self.client.wline("PRIVMSG P@cservice.netgamers.org :recover %s %s " %
                                  (self.desired_nick, self.config.get("IRC", "auth")))
                self.client.wline("NICK %s" % self.desired_nick)

    def random_nick(self):
        nick = random.choice(string.ascii_letters)
        for _ in xrange(14):
            nick += random.choice(string.ascii_letters + string.digits)
        return nick
