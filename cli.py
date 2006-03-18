import socket,string,re,time

CRLF = "\r\n"
DEBUG = 1

class connection:
  "Client wrapper class for IRC server command line interface"
  NOTICE_PREFIX = 1
  PUBLIC_PREFIX = 2
  PRIVATE_PREFIX = 3
  
  def __init__ (self, host, port):
    "Connect to an IRC hub"

  def connect(self):
	"do nowt"

  def wline(self, line):
    "Send a line to the hub"
    print line

  def rline(self):
    "text"

  def privmsg(self,target,text):
    self.wline("PRIVMSG %s :%s" % (target, text))
    pass

  def notice(self,target,text):
    self.wline("NOTICE %s :%s" % (target, text))
    pass
  
  def reply(self,prefix,nick,target,text):
    if prefix == self.NOTICE_PREFIX:
      self.wline("NOTICE %s :%s" % (nick, text))
    if prefix == self.PUBLIC_PREFIX:
      m=re.match(r"(#\S+)",target,re.I)
      if m:
        self.wline("PRIVMSG %s :%s" % (target, text))
      else:
        prefix = self.PRIVATE_PREFIX
    if prefix == self.PRIVATE_PREFIX:
      self.wline("PRIVMSG %s :%s" % (nick, text))
      
      
  
