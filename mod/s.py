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
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"\s+(.*)")
        self.paramre=re.compile(r"^(\d+)(\s+(\S+))?")
        
        self.usage=self.__class__.__name__ + " <id> [status]"
        self.helptext=["Show or set the status of a defence call. Valid statuses include covered, uncovered, recheck, impossible, invalid, semicovered, recall and fake."]

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0
        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        u=loadable.user(pnick=user)
        if not u.load_from_db(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
            return 1

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        
        # assign param variables 
        call_id=m.group(1)
        s_command=m.group(3)
        
        # do stuff here
        d=loadable.defcall(call_id)
        if not d.load_most_recent(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"No defcall matching id %s found" %(call_id,))
            return 0
        
        p=d.actual_target
        
        if not s_command:
            self.client.reply(prefix,nick,target,str(d))
            return 1
        
        query="SELECT id, status FROM defcall_status WHERE status ilike %s"
        self.cursor.execute(query,(s_command+'%',))
        s=self.cursor.dictfetchone()
        if not s:
            self.client.reply(prefix,nick,target,"%s is not a valid defcall status, defcall was not modified"%(s_command,))
            return 0
        
        query="UPDATE defcalls SET status = %s,claimed_by=%s WHERE id = %s"
        print str(u.id)
        self.cursor.execute(query,(s['id'],user,d.id))
        if self.cursor.rowcount < 1:
            self.client.reply(prefix,nick,target,"Something went wrong. Old status was %s, new status was %s, defcall id was %s"%(old_status,s['status'],d.id))
        else:
            self.client.reply(prefix,nick,target,
                              "Updated defcall %s on %s:%s:%s landing pt %s from status '%s' to '%s'"%(d.id,p.x,p.y,p.z,d.landing_tick,d.actual_status,s['status']))
        
        return 1
