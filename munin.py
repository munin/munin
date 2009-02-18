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
            raise ValueError("Expected configuration in muninrc, not found.")

        self.client = connection(config)
        self.handler = parser(config, self.client,self)

        while True:
            try:
                self.reboot()
            except Exception, e:
                print "Exception during command: " + e.__str__()

    def reboot(self):
        self.ircu_router=irc_router(self.client,self.config,self.reboot)
        self.irc_router.run()

ofile=file("pid.munin", "w")
ofile.write("%s" % (os.getpid(),))
ofile.close()
    
munin()

