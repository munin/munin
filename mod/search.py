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

# Nothing alliance specific in this module as far as I can tell.
# qebab, 24/6/08.

class search(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,50)
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + " <alliance|nick>" 
        
    def execute(self,nick,target,prefix,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0
        
        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        
        # assign param variables
        params=m.group(1)

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        
        # do stuff here
        args=('%'+params+'%','%'+params+'%')
        query="SELECT t1.x AS x,t1.y AS y,t1.z AS z,t1.size AS size,t1.score AS score,t1.value AS value,t1.race AS race,t4.name AS alliance,t2.nick AS nick,t2.reportchan AS reportchan,t2.comment AS comment"
        query+=" FROM planet_dump AS t1 INNER JOIN planet_canon AS t3 ON t1.id=t3.id"
        query+=" INNER JOIN intel AS t2 ON t3.id=t2.pid"
        query+=" LEFT JOIN alliance_canon AS t4 ON t2.alliance_id=t4.id"
        query+=" WHERE t1.tick=(SELECT MAX(tick) FROM updates) AND (t4.name ILIKE %s OR t2.nick ILIKE %s)"
        self.cursor.execute(query,args)

        i=0
        planets=self.cursor.dictfetchall()
        if not len(planets):
            reply="No planets in intel matching nick or alliance: %s"%(params,)
            irc_msg.reply(reply)
            return 1
        for p in planets:
            reply="%s:%s:%s (%s)" % (p['x'],p['y'],p['z'],p['race'])
            reply+=" Score: %s Value: %s Size: %s" % (p['score'],p['value'],p['size'])
            if p['nick']:
                reply+=" Nick: %s" % (p['nick'],)
            if p['alliance']:
                reply+=" Alliance: %s" % (p['alliance'],)
            if p['reportchan']:
                reply+=" Reportchan: %s" % (p['reportchan'],)
            if p['comment']:
                reply+=" Comment: %s" % (p['comment'],)
            i+=1
            if i>4 and len(planets)>4:
                reply+=" (Too many results to list, please refine your search)"
                irc_msg.reply(reply)
                break
            irc_msg.reply(reply)

                                
        
        return 1
                                                                                                                                            
    def split_opts(self,params):
        param_dict={}
        active_opt=None
        for s in params.split('='):
            if active_opt:
                m=self.optionsre[active_opt].search(s)
                if m:
                    param_dict[active_opt]=m.group(1)
            last_act=active_opt
            for key in self.optionsre.keys():
                if s.endswith(" "+key):
                    active_opt=key
            if active_opt == last_act:
                active_opt=None
        return param_dict
