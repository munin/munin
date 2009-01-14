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

import time

import re
import socket

CRLF = "\r\n"
DEBUG = 1

class connection:
  "Client wrapper class for IRC server"
  NOTICE_PREFIX = 1
  PUBLIC_PREFIX = 2
  PRIVATE_PREFIX = 3
  
  def __init__ (self, host, port):
    "Connect to an IRC hub"
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.settimeout(300)
    self.host=host
    self.port=port
    self.pingre=re.compile(r"PING\s*:\s*(\S+)",re.I)
    self.pongre=re.compile(r"PONG\s*:",re.I)
    self.lastcommand=0

  def connect(self):
    self.sock.connect((self.host, self.port))
    self.file = self.sock.makefile("rb")


  def wline(self, line):
    "Send a line to the hub"
    m=self.pongre.search(line)
    if m:
      self.sock.send(line + CRLF)
    else:
      if DEBUG:
        print ">>>", line;
      while self.lastcommand + 2 >= time.time():
        time.sleep(0.1)
      self.sock.send(line+CRLF)
      self.lastcommand=time.time()

  def rline(self):
    "Read a line from the server"
    line = self.file.readline()
    if not line:
      return line
    if line[-2:] == CRLF:
      line = line[:-2]
    if line[-1:] in CRLF:
      line = line[:-1]
    m=self.pingre.search(line)
    if m:
      self.wline("PONG :%s" % m.group(1))
      return line

    if DEBUG:
      print "<<<", line;
    return line

  def privmsg(self,target,text):
    while len(text) > 0:
      self.wline("PRIVMSG %s :%s" % (target,text[:440]))
      text=text[440:]
    
  def notice(self,target,text):
    while len(text) > 0:
      self.wline("NOTICE %s :%s" % (target, text[:440]))
      text=text[440:]
      
  def reply(self,prefix,nick,target,text):
    if prefix == self.NOTICE_PREFIX:
      self.notice(nick,text)
    if prefix == self.PUBLIC_PREFIX:
      m=re.match(r"(#\S+)",target,re.I)
      if m:
        self.privmsg(target,text)
        #self.wline("PRIVMSG %s :%s" % (target, text))
      else:
        prefix = self.PRIVATE_PREFIX
    if prefix == self.PRIVATE_PREFIX:
      self.privmsg(nick,text)
      #self.wline("PRIVMSG %s :%s" % (nick, text))
      
      
  
