#!/usr/bin/python -u

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

import os
import ConfigParser

from connection import connection
from parser import parser

class munin:
    def __init__(self):
        config = ConfigParser.ConfigParser()
        if not config.read('muninrc'):
            # No configfile. What to do?
            raise ValueError("Expected configuration in muninrc, "
                             "not found.")
        self.server = config.get("IRC", "server")
        self.port = int(config.get("IRC", "port"))
        self.nick = config.get("IRC", "nick")
        self.user = config.get("IRC", "user")
        self.ircname = config.get("IRC", "name")

        self.client = connection(self.server, self.port)
        self.handler = parser(self.client,self)
        self.client.connect()
        self.run()
        
    def run(self):
        self.client.wline("NICK %s" % self.nick)
        self.client.wline("USER %s 0 * : %s" % (self.user,self.ircname))
        
        while 1:
            line = self.client.rline()
            if not line:
                break
            debug=self.handler.parse(line)
            if debug:
                print debug



ofile=file("pid.munin", "w")
ofile.write("%s" % (os.getpid(),))
ofile.close()

    
munin()

