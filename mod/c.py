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

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08

class c(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"\s+(.*)")
        self.paramre=re.compile(r"^(\d+)(\s+(.+))?")
        
        self.usage=self.__class__.__name__ + " <id> [comment]"
        self.helptext=["Show or set the comment of a defence call. "]

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        u=loadable.user(pnick=irc_msg.user)
        if not u.load_from_db(self.cursor):
            irc_msg.reply("You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
            return 1

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        
        # assign param variables 
        call_id=m.group(1)
        new_comment=m.group(3)
        
        # do stuff here
        d=loadable.defcall(call_id)
        if not d.load_most_recent(self.cursor):
            irc_msg.reply("No defcall matching id %s found" %(call_id,))
            return 0
        
        c=d.comment
        
        if not new_comment:
            if not c:
                reply="Defcall %s has no comment"%(d.id,)
            else:
                reply="Defcall %s has comment '%s'"%(d.id,c)
            irc_msg.reply(reply)
            return 1
        
        query="UPDATE defcalls SET comment=%s WHERE id=%s"
        args=(new_comment,d.id)
        
        self.cursor.execute(query,args)
        
        if self.cursor.rowcount < 1:
            irc_msg.reply("Something went wrong. Defcall id was %s and new comment was '%s'"%(d.id,new_comment))
        else:
            p=d.actual_target
            irc_msg.reply(
                              "Updated defcall %s on %s:%s:%s landing pt %s with comment '%s'"%(d.id,p.x,p.y,p.z,d.landing_tick,new_comment))
        
        return 1
