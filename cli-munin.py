#!/usr/bin/python

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