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

class irc_message(object):
    def __init__(self,client=None,cursor=None,line=None,nick=None,username=None,host=None,target=None,message=None,prefix=None,command=None):
        self.notprefix=r"~|-|\."
        self.pubprefix=r"!"
        self.privprefix='@'
        self.privmsgre=re.compile(r"^:(\S+)!(\S+)@(\S+)\s+PRIVMSG\s+(\S+)\s+:(\s*(%s|%s|%s)(.*?)\s*)$" %(self.notprefix,self.pubprefix,self.privprefix))
        self.pnickre=re.compile(r"(\S{2,15})\.users\.netgamers\.org")
        self.client=client
        self.cursor=cursor
        self.command=None

        m=self.privmsgre.search(line)
        if m:
            self.nick=m.group(1)
            self.username=m.group(2)
            self.host=m.group(3)
            self.target=m.group(4)
            self.message=m.group(5)
            self.prefix=m.group(6)
            self.command=m.group(7)
            self.user=self.getpnick(self.host)
            self.access=self.getaccess(self.user,target)

    def reply(self,message):
        self.client.reply(prefix,nick,target,message)

    def prefix_numeric(self):
        if self.notprefix.replace("|","").find(self.prefix) > -1:
            return self.client.NOTICE_PREFIX
        if self.pubprefix.replace("|","").find(self.prefix) > -1:
            return self.client.PUBLIC_PREFIX
        if self.privprefix.replace("|","").find(self.prefix) > -1:
            return self.client.PRIVATE_PREFIX
        return -1

    def prefix_notice(self):
        return self.notprefix.replace("|","").find(self.prefix) > -1

    def prefix_private(self):
        return self.privprefix.replace("|","").find(self.prefix) > -1


    def reply(self,text):
        self.client.reply(self.prefix_numeric(),self.nick,self.target,text)

    def match_command(self,regexp):
        return regexp.search(self.command)
    def user_or_nick(self):
        return self.user or self.nick

    def getpnick(self,host):
        m=self.pnickre.search(host)
        if m:
            return m.group(1)
        else:
            return None

    def getaccess(self,user,target):
        query="SELECT * FROM access_level(%s,%s,%d)"
        self.cursor.execute(query,(user,target,self.prefix_notice() or self.prefix_private()))
        access=self.cursor.dictfetchone()['access_level'] or 0
        return access
