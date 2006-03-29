#!/usr/bin/python -u

import os

from connection import connection
from parser import parser

class munin:
    def __init__(self):
        self.server = '80.232.65.133'
        self.port = 6667
        self.nick = 'Munin'
        self.user = 'raven'
        self.ircname = '<insert wit here>'

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

