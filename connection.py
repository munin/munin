import socket,string,re,time

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
      while self.lastcommand + 1.5 >= time.time():
        time.sleep(0.1)
      while len(line) > 0:
        self.sock.send(line[:512] + CRLF)
        line=line[512:]
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
      
      
  
