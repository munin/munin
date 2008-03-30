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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA 
 
# This work is Copyright (C)2006 by Andreas Jacobsen  
# Individual portions may be copyright by individual contributors, and

# are included in this collective work with permission of the copyright  
# owners. 



class con(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + ""
	self.helptext=None

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0


        reply="Optimal construction worker/shipwrights settings: 1% (-1), 9% (-2), 17% (-3), 26% (-4), 34% (-5). Add your racial bonus to get your total construction/production time bonus. If your construction worker settings are not one of these percentages, you should apply to join Angels or Wolfpack."

        self.client.reply(prefix,nick,target,reply)

        return 1
