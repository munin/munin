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

class message:
    
    def __init__(self,client=None,nick=None,username=None,host=None,target=None,message=None,prefix_numeric=None,command=None,user=None,access=None,client=None):
        self.notprefix=r"~|-|\."
        self.pubprefix=r"!"
        self.privprefix='@'

        self.client=client

        self.nick=nick
        self.username=username
        self.host=host
        self.target=target
        self.message=message
        self.prefix_numeric=prefix_numeric
        self.command=command
        self.user=user
        self.access=access
        self.client=client

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

    def reply(self,text):
        self.client.reply(prefix_numeric(),nick,target,text)
