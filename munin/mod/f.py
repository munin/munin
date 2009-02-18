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

# This module has no alliance specific things as far as I can tell.
# qebab, 24/6/08.

class f(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"\s+(.*)")
        self.paramre=re.compile(r"^(\d+)(\s+(\S+))?(\s+(.*))?")
        self.etare=re.compile(r"(\d+)")
        self.usage=self.__class__.__name__ + " <id> [status]"
        self.usage_eta=self.__class__.__name__+" <id> <eta|land> <eta|landing_tick>"
        self.usage_oeta=self.__class__.__name__+" <id> <oeta|launch> <original_eta|launch_tick>"
        self.helptext=["Show or modify the status of a fleet. Possible modifications include eta/land to modify landing tick, oeta/launch to modify original eta/launch tick or delete to delete the fleet."]

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        # assign param variables
        fleet_id=m.group(1)
        s_command=m.group(3)
        sub_params=m.group(5)

        # do stuff here
        f=loadable.fleet(fleet_id)
        if not f.load_most_recent(self.cursor):
            irc_msg.reply("No fleet matching id %s found" %(fleet_id,))
            return 0

        if not s_command:
            irc_msg.reply(str(f))
            return 1
        elif "eta".startswith(s_command) or "land".startswith(s_command):
            new_eta = self.extract_eta(sub_params or "")
            if not new_eta:
                irc_msg.reply("Usage: %s"%(self.usage_eta,))
                return 0
            self.cmd_eta(f,new_eta)
        elif "oeta".startswith(s_command) or "launch".startswith(s_command):
            new_orig_eta = self.extract_eta(sub_params or "")
            if not new_orig_eta:
                irc_msg.reply("Usage: %s"%(self.usage_oeta,))
                return 0
            self.cmd_orig_eta(f,new_orig_eta)
        elif "delete".startswith(s_command):
            return self.cmd_delete(f)
        else:
            irc_msg.reply("s_command %s"%(s_command,))
        return 1

    def extract_eta(self,sub_params):
        m=self.etare.search(sub_params)
        if not m:
            return None
        else:
            return int(m.group(1))

    def cmd_eta(self,f,when):
        curtick=self.current_tick()
        if when < 80:
            tick=curtick+when
            eta=when
        else:
            tick=when
            eta=tick-curtick
        if tick > 32767:
            tick=32767

        query="UPDATE fleet SET landing_tick=%s WHERE id=%s"
        args=(tick,f.id)
        self.cursor.execute(query,args)
        if self.cursor.rowcount < 1:
            irc_msg.reply("Could not update ETA for fleet with id %s, no matching fleets found"%(f.id,))
        else:
            irc_msg.reply("Updated landing tick for fleet id %s from %s to %s (new eta is %s)"%(f.id,f.landing_tick,tick,eta))
        return 1


    def cmd_orig_eta(self,f,when):

        if when < 80:
            tick=f.landing_tick-when
            eta=when
        else:
            tick=when
            eta=f.landing_tick-tick
        if tick > 32767:
            tick=32767

        query="UPDATE fleet SET launch_tick=%s WHERE id=%s"
        args=(tick,f.id)
        self.cursor.execute(query,args)
        if self.cursor.rowcount < 1:
            irc_msg.reply("Could not update original ETA for fleet with id %s, no matching fleets found"%(f.id,))
        else:
            irc_msg.reply("Updated launch tick for fleet id %s from %s to %s (new original eta is %s)"%(f.id,f.launch_tick,tick,eta))
        return 1

    def cmd_delete(self,f):
        query="DELETE FROM fleet WHERE id=%s"

        self.cursor.execute(query,(f.id,))

        if self.cursor.rowcount < 1:
            irc_msg.reply("Couldn't delete fleet matching id %s, weird.")
            return 0

        reply="Deleted %s"%(str(f),)

        irc_msg.reply(reply)

        return 1

        query="SELECT id, status FROM defcall_status WHERE status ilike %s"
        self.cursor.execute(query,(s_command+'%',))
        s=self.cursor.dictfetchone()
        if not s:
            irc_msg.reply("%s is not a valid defcall status, defcall was not modified"%(s_command,))
            return 0

        query="UPDATE defcalls SET status = %s,claimed_by=%s WHERE id = %s"

        self.cursor.execute(query,(s['id'],u.id,d.id))
        if self.cursor.rowcount < 1:
            irc_msg.reply("Something went wrong. Old status was %s, new status was %s, defcall id was %s"%(old_status,s['status'],d.id))
        else:
            irc_msg.reply("Updated defcall %s on %s:%s:%s landing pt %s from status '%s' to '%s'"%(d.id,p.x,p.y,p.z,d.landing_tick,d.actual_status,s['status']))

        return 1
