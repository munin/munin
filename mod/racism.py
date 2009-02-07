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



class racism(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,50)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + " [alliance] (All information taken from intel, for tag information use the lookup command)"
        self.help=['Shows averages for each race matching a given alliance in intel.']

    def execute(self,nick,target,command,user,access,irc_msg):
        m=self.commandre.search(command)
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
        
        alliance=m.group(1)
        
        query="SELECT count(*) AS members, sum(t1.value) AS tot_value, sum(t1.score) AS tot_score, sum(t1.size) AS tot_size, sum(t1.xp) AS tot_xp, t1.race AS race"
        query+=" FROM planet_dump AS t1"
        query+=" INNER JOIN intel AS t2 ON t1.id=t2.pid"
        query+=" LEFT JOIN alliance_canon t3 ON t2.alliance_id=t3.id"
        query+=" WHERE t1.tick=(SELECT MAX(tick) FROM updates) AND t3.name ILIKE %s"
        query+=" GROUP BY t3.name ILIKE %s, t1.race ORDER by t1.race ASC"

        self.cursor.execute(query,('%'+alliance+'%','%'+alliance+'%'))
        reply=""
        if self.cursor.rowcount<1:
            reply="Nothing in intel matches your search '%s'" % (alliance,)
        else:
            results=self.cursor.dictfetchall()
            reply="Demographics for %s: "%(alliance,)
            reply+=string.join(map(self.profile,results),' | ')
        irc_msg.reply(reply)
        
        return 1
    
    def profile(self,res):
        reply="%s %s Val(%s)" % (res['members'],res['race'],self.format_real_value(res['tot_value']/res['members']))
        reply+=" Score(%s)" % (self.format_real_value(res['tot_score']/res['members']),)
        reply+=" Size(%s) XP(%s)" % (res['tot_size']/res['members'],self.format_real_value(res['tot_xp']/res['members']))
        return reply
