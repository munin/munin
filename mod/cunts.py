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

# I think I removed the ascendancy specific from this module.
# qebab - 24/6/08

class cunts(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.paramre=re.compile("\s+(.*)")
#        re.compile(r"(\s+(\S+))?(\s+(ter|cat|xan|zik))(\s+(<|>)?(\d+))?(\s+(<|>)?(\d+))?",re.I)
        self.alliancere=re.compile(r"^(\S+)$")
        self.racere=re.compile(r"^(ter|cat|xan|zik|eit|etd)$",re.I)
        self.rangere=re.compile(r"^(<|>)?(\d+)$")
        self.bashre=re.compile(r"^(bash)$",re.I)
        self.clusterre=re.compile(r"^c(\d+)$",re.I)
        self.usage=self.__class__.__name__ + " [alliance] [race] [<|>][size] [<|>][value] [bash]" + " (must include at least one search criteria, order doesn't matter)"
        self.helptext=["Lists planets currently attacking %s planets (as per intel). Sorts by size. This command is a bit spammy and will probably highlight people, so please do it in private or with a private command prefix." % self.config.get("Auth", "alliance")]
        
    def execute(self,nick,target,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        
        # assign param variables
        
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        alliance=None
        race=None
        size_mod=None
        size=None
        value_mod=None
        value=None
        bash=False
        attacker=None
        cluster=None
        
        param=m.group(1)
        params=param.split()

        for p in params:
            m=self.bashre.search(p)
            if m and not bash:
                bash=True
                continue
            m=self.clusterre.search(p)
            if m and not cluster:
                cluster=int(m.group(1))
            m=self.racere.search(p)
            if m and not race:
                race=m.group(1)
                continue
            m=self.rangere.search(p)
            if m and not size and int(m.group(2)) < 32768:
                size_mod=m.group(1) or '>' 
                size=m.group(2)
                continue
            m=self.rangere.search(p)
            if m and not value:
                value_mod=m.group(1) or '<'
                value=m.group(2)
                continue
            m=self.alliancere.search(p)
            if m and not alliance and not self.clusterre.search(p):
                alliance=m.group(1) 
                continue



        if bash:
            if not user:
                irc_msg.reply("You must be registered to use the "+self.__class__.__name__+" command's bash option (log in with P and set mode +x)")
                return 1
            u=loadable.user(pnick=user)
            if not u.load_from_db(irc_msg.client,self.cursor):
                irc_msg.reply("Usage: %s (you must set your planet in preferences to use the bash option (!pref planet=x:y:z))" % (self.usage,))
                return 1
            if u.planet_id:
                attacker = u.planet
            else:
                irc_msg.reply("Usage: %s (you must set your planet in preferences to use the bash option (!pref planet=x:y:z))" % (self.usage,))
                return 1
        
        victims=self.cunts(alliance,race,size_mod,size,value_mod,value,attacker,bash,cluster)
        
        i=0
        if not len(victims):
            reply="No"
            if race:
                reply+=" %s"%(race,)
            reply+=" planets attacking %s" % self.config.get('Auth', 'alliance')
            if alliance:
                reply+=" in intel matching Alliance: %s"%(alliance,)
            else:
                reply+=" matching"
            if size:
                reply+=" Size %s %s" % (size_mod,size)
            if value:
                reply+=" Value %s %s" % (value_mod,value)
            if cluster:
                reply+=" Cluster %s" %(cluster,)
            irc_msg.reply(reply)
        for v in victims:
            reply="%s:%s:%s (%s)" % (v['x'],v['y'],v['z'],v['race'])
            reply+=" Value: %s Size: %s" % (v['value'],v['size'])
            if v['nick']:
                reply+=" Nick: %s" % (v['nick'],)
            if not alliance and v['alliance']:
                reply+=" Alliance: %s" % (v['alliance'],)
            targs=self.attacking(v['pid'])
            if targs:
                reply+=" Hitting: "
                print targs
                a=[]
                for t in targs:
                    if t:
                        a.append((t['nick'] or 'Unknown') + " (%s, lands: %s)"% (t['fleet_size'],t['landing_tick']))
                        
                reply+=', '.join(a)
            i+=1
            if i>4 and len(victims)>4:
                reply+=" (Too many victims to list, please refine your search)"
                irc_msg.reply(reply)
                break
            irc_msg.reply(reply)
        
        
        return 1

    def cunts(self,alliance=None,race=None,size_mod='>',size=None,value_mod='<',value=None,attacker=None,bash=None,cluster=None):
        args=()

        query="SELECT DISTINCT t1.id AS pid,t1.x AS x,t1.y AS y,t1.z AS z,"
        query+="t1.size AS size,t1.size_rank AS size_rank,t1.value AS value,"
        query+="t1.value_rank AS value_rank,t1.race AS race,"
        query+="t6.name AS alliance,t2.nick AS nick"
        #query+="t3.landing_tick AS landing_tick, t4.size*.25 AS potential_gain,"
        #query+="t6.nick AS target_nick"
        query+=" FROM planet_dump AS t1"
        query+=" LEFT JOIN intel AS t2 ON t1.id=t2.pid"
        query+=" INNER JOIN fleet AS t3 ON t1.id=t3.owner_id"
        #query+=" INNER JOIN intel AS t6 ON t3.target=t6.pid"
        query+=" LEFT JOIN alliance_canon AS t6 ON t2.alliance_id=t6.id"
        query+=" WHERE t1.tick=(SELECT max_tick())"
        #query+=" AND t4.tick=(SELECT max_tick())"
        query+=" AND t3.landing_tick>(SELECT max_tick())"
        query+=" AND t3.mission ilike 'attack'"
        query+=" AND t3.target IN ("
        query+=" SELECT t5.pid FROM intel AS t5 "
        query+=" LEFT JOIN alliance_canon AS t7 ON t5.alliance_id=t7.id"
        query+=" WHERE t7.name ilike %s) " #% self.config.get('Auth', 'alliance')
        args += (self.config.get('Auth', 'alliance'),)
        if alliance:
            query+=" AND t6.name ILIKE %s"
            args+=('%'+alliance+'%',)
        if race:
            query+=" AND race ILIKE %s"
            args+=(race,)
        if size:
            query+=" AND size %s " % (size_mod) + "%s"
            args+=(size,)
        if value:
            query+=" AND value %s " % (value_mod) + "%s"
            args+=(value,)
        if bash:
            query+=" AND (value > %s OR score > %s)"
            args+=(attacker.value*.4,attacker.score*.6)
        if cluster:
            query+=" AND x = %s::smallint"
            args+=(cluster,)
                            
        query+=" ORDER BY t1.size DESC, t1.value DESC"
        self.cursor.execute(query,args)
        return self.cursor.dictfetchall()

    def attacking(self,pid):
        query="SELECT DISTINCT t2.nick AS nick, t1.fleet_size, t1.landing_tick FROM fleet AS t1"
        query+=" INNER JOIN intel AS t2 ON t1.target=t2.pid"
        query+=" WHERE t1.owner_id = %s"
        query+=" AND t1.landing_tick > (select max_tick())"
        self.cursor.execute(query,(pid,))
        return self.cursor.dictfetchall()
