"""
Loadable.Loadable subclass
"""

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

class addquote(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.paramre=re.compile(r"^\s+(.*)$")
        self.timestampre=re.compile(r"\s*\[?\s*\d+:\d+(:\d+)?\s*\]?\s*")
        self.usage=self.__class__.__name__ + " <quote goes here>"

    def execute(self,nick,host,target,prefix,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        m=self.paramre.search(m.group(1))

        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        params=m.group(1)        
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        params=self.striptimestamps(params)
        args=(params,)

        query="INSERT INTO quote (quote) VALUES (%s)"
        self.cursor.execute(query,args)
        #reply="Added your shitty quote"    
        #irc_msg.reply(reply)
        
        irc_msg.reply("Added your shitty quote: "+params)
        # do stuff here
        
        return 1
    
    def striptimestamps(self,s):
        """
        strip timestamps from s
        """
        s=self.timestampre.sub(' ',s)
        s=s.strip()
        return s
