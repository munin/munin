#!/usr/bin/python

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

import os, sys

from cli import connection
from parser import parser

class munin:
    def __init__(self, command):
        self.server = 'irc.netgamers.org'
        self.port = 6667
        self.nick = 'Munin'
        self.user = 'raven'
        self.ircname = '<insert wit here>'

        self.client = connection(self.server, self.port)
        self.handler = parser(self.client,self)
        self.client.connect()
        self.run(command)
        
    def run(self, command):
        self.client.wline("NICK %s" % self.nick)
        self.client.wline("USER %s 0 * : %s" % (self.user,self.ircname))
        
        debug=self.handler.parse(':jesterina!sodoff@jester.users.netgamers.org PRIVMSG #ascendancy :!' + command)
        if debug:
            print debug

args = sys.argv

command = ''
flag = 0
for p in args:
    if flag == 1:
        command = p
    elif flag != 0:
        command = command + ' '+  p
    flag = flag + 1
    
munin(command)