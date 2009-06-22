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

class auth(object):
    def __init__(self,client,config):
        self.client = client
        self.config = config
        self.welcomre=re.compile(r"\S+\s+(001|433).*",re.I)
        self.pinvitere=re.compile(r"^:P!cservice@netgamers.org\s+INVITE\s+\S+\s+:#(\S+)",re.I)
    def message(self,line):
        m=self.welcomre.search(line)
        if m:
            if self.config.has_option("IRC","auth"):
                self.client.wline("PRIVMSG P@cservice.netgamers.org :recover %s %s " % (self.config.get('Connection','nick'),self.config.get("IRC", "auth")))
                self.client.wline("PRIVMSG P@cservice.netgamers.org :auth %s" % (self.config.get("IRC", "auth")))
            if self.config.has_option("IRC", "modes"): self.client.wline("MODE %s +%s" % (self.config.get("Connection",'nick'), self.config.get("IRC", "modes")))
            return
        m=self.pinvitere.search(line)
        if m:
            self.client.wline("JOIN #%s" % m.group(1))
            return

