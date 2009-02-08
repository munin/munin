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

# Nothing alliance specific found in this module.
# qebab, 24/6/08.

class s(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"\s+(.*)")
        self.paramre=re.compile(r"^(\d+)(\s+(\S+))?")
        
        self.usage=self.__class__.__name__ + " <id> [status]"
        self.helptext=["Show or set the status of a defence call. Valid statuses include covered, uncovered, recheck, impossible, invalid, semicovered, recall and fake."]

    def execute(self,nick,target,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        u=loadable.user(pnick=user)
        if not u.load_from_db(irc_msg.client,self.cursor):
            irc_msg.reply("You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
            return 1

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        
        # assign param variables 
        call_id=m.group(1)
        s_command=m.group(3)
        
        # do stuff here
        d=loadable.defcall(call_id)
        if not d.load_most_recent(irc_msg.client,self.cursor):
            irc_msg.reply("No defcall matching id %s found" %(call_id,))
            return 0
        
        p=d.actual_target
        
        if not s_command:
            irc_msg.reply(str(d))
            return 1
        
        query="SELECT id, status FROM defcall_status WHERE status ilike %s"
        self.cursor.execute(query,(s_command+'%',))
        s=self.cursor.dictfetchone()
        if not s:
            irc_msg.reply("%s is not a valid defcall status, defcall was not modified"%(s_command,))
            return 0
        
        query="UPDATE defcalls SET status = %s,claimed_by=%s WHERE id = %s"
        print str(u.id)
        self.cursor.execute(query,(s['id'],user,d.id))
        if self.cursor.rowcount < 1:
            irc_msg.reply("Something went wrong. Old status was %s, new status was %s, defcall id was %s"%(old_status,s['status'],d.id))
        else:
            irc_msg.reply(
                              "Updated defcall %s on %s:%s:%s landing pt %s from status '%s' to '%s'"%(d.id,p.x,p.y,p.z,d.landing_tick,d.actual_status,s['status']))
        
        return 1
