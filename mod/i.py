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

# Nothing alliance specific in this module as far as I can tell.
# qebab, 24/6/08.

class i(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"\s+(.*)")
        self.paramre=re.compile(r"^(\d+)")
        
        self.usage=self.__class__.__name__ + " <id> "
        self.helptext=["Show the fleets on a defence call. Remember that this information might be dodgy, so remember to check scans or galstatus to confirm ETAs."]

    def execute(self,nick,target,prefix,command,user,access,irc_msg):
        m=self.commandre.search(command)
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
        
        # do stuff here
        d=loadable.defcall(call_id)
        if not d.load_most_recent(irc_msg.client,self.cursor):
            irc_msg.reply("No defcall matching id %s found" %(call_id,))
            return 0
        
        query="SELECT t1.id AS fleet_id, t4.id AS defcall_id"
        query+=", t2.race AS race, t2.x AS owner_x, t2.y AS owner_y, t2.z AS owner_z"
        query+=", t3.x AS target_x, t3.y AS target_y, t3.z AS target_z"
        query+=", t1.fleet_size AS fleet_size, t1.fleet_name AS fleet_name"
        query+=", t1.landing_tick AS landing_tick, t1.mission AS mission"
        query+=" FROM fleet AS t1"
        query+=" INNER JOIN planet_dump AS t2 ON t1.owner_id=t2.id"
        query+=" INNER JOIN planet_dump AS t3 ON t1.target=t3.id"
        query+=" INNER JOIN defcalls AS t4"
        query+=" ON t1.target=t4.target AND t1.landing_tick=t4.landing_tick"
        query+=" WHERE t2.tick = (SELECT max_tick()) AND t3.tick = (SELECT max_tick())"
        query+=" AND t4.id=%d"
        
        self.cursor.execute(query,(int(d.id),))
        
        if self.cursor.rowcount < 1:
            irc_msg.reply("No fleets found for defcall with ID '%s'"%(call_id,))
            return 1
        
        all=self.cursor.dictfetchall()
        reply="Fleets hitting %s:%s:%s as part of defcall %s"%(d.actual_target.x,
                                                               d.actual_target.y,
                                                               d.actual_target.z,
                                                               d.id)
        reply+=" with eta %d"%(d.landing_tick-self.current_tick(),)
        irc_msg.reply(reply)
        
        for s in all:
            reply="-> (id: %s) from %s:%s:%s (%s)"%(s['fleet_id'],s['owner_x'],s['owner_y'],s['owner_z'],s['race'])
            reply+=" named '%s' with %s ships set to %s"%(s['fleet_name'],s['fleet_size'],s['mission'])
            irc_msg.reply(reply)
            
        
        
        return 1
