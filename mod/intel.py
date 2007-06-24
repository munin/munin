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

import string

class intel(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + " <x:y:z> [option=value]+"
        self.planet_coordre=re.compile(r"(\d+)[. :-](\d+)[. :-](\d+)(.*)")
        self.gal_coordre=re.compile(r"(\d+)[. :-](\d+)")
        self.optionsre={}
        self.optionsre['nick']=re.compile("^(\S+)")
        self.optionsre['fakenick']=re.compile("^(\S+)")
        self.optionsre['alliance']=re.compile("^(\S+.*?)(\s+\S+)?$")
        self.optionsre['reportchan']=re.compile("^(\S+)")
        self.optionsre['relay']=re.compile("^(t|f)",re.I)
        self.optionsre['hostile_count']=re.compile("^(\d+)")
        self.optionsre['scanner']=re.compile("^(t|f)",re.I)
        self.optionsre['distwhore']=re.compile("^(t|f)",re.I)
	self.optionsre['nap']=re.compile("^(t|f)",re.I)
        self.optionsre['comment']=re.compile("^(.*)")                
        options=self.optionsre.keys()
        options.sort()
        self.helptext=["Valid options: %s" % (string.join(options,', '))]

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 1

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 1
        
        #assign param variables
        par=m.group(1)
        m=self.planet_coordre.search(par)
        if not m:
            m=self.gal_coordre.search(par)
            if m:
                return self.exec_gal(nick,username,host,target,prefix,command,user,access,m.group(1),m.group(2))
            else:
                self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
                return 1
        
        p=loadable.planet(x=m.group(1),y=m.group(2),z=m.group(3))

        params=m.group(4)
        
        if not p.load_most_recent(self.conn,self.client,self.cursor):
            self.client.reply(prefix,nick,target,"No planet matching '%s:%s:%s' found"%(p.x,p.y,p.z,))
            return 1

        i=loadable.intel(pid=p.id)
        if not i.load_from_db(self.conn,self.client,self.cursor):
            #self.client.reply(prefix,nick,target,"No planet matching '%s:%s:%s' found"%(p.x,p.y,p.z,))
            #return 1
            pass

        opts=self.split_opts(params)
        opts['pid']=p.id

        for k in self.optionsre.keys():
            if not opts.has_key(k):
                opts[k]=getattr(i,k)
        if opts['alliance']:
	    a=loadable.alliance(name=opts['alliance'])
	    if not a.load_from_db:
		del opts['alliance']
		a=loadable.alliance(id=None)
	else:
	    a=loadable.alliance(id=None)

        if i.id > 0:
            query="UPDATE intel SET "
            query+="pid=%s,nick=%s,fakenick=%s,alliance_id=%s,relay=%s,reportchan=%s,hostile_count=%s,"
            query+="scanner=%s,distwhore=%s,comment=%s"
            query+=" WHERE id=%s"
            self.cursor.execute(query,(opts['pid'],opts['nick'],
                                       opts['fakenick'],a.id,opts['relay'],
                                       opts['reportchan'],opts['hostile_count'],
                                       opts['scanner'],opts['distwhore'],opts['comment'],i.id))
            
        elif params:
            query="INSERT INTO intel (pid,nick,fakenick,relay,reportchan,hostile_count,scanner,distwhore,comment,alliance_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            self.cursor.execute(query,(opts['pid'],opts['nick'],
                                       opts['fakenick'],opts['relay'],
                                       opts['reportchan'],opts['hostile_count'],
                                       opts['scanner'],opts['distwhore'],
				       opts['comment'],a.id))
        i=loadable.intel(pid=opts['pid'],nick=opts['nick'],fakenick=opts['fakenick'],
                         alliance=opts['alliance'],relay=opts['relay'],reportchan=opts['reportchan'],
                         hostile_count=opts['hostile_count'],scanner=opts['scanner'],
                         distwhore=opts['distwhore'],comment=opts['comment'])

        reply="Information stored for %s:%s:%s - "% (p.x,p.y,p.z)
        reply+=i.__str__()
        self.client.reply(prefix,nick,target,reply)
        
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
    
#    def help(self):



    def exec_gal(self,nick,username,host,target,prefix,command,user,access,x,y):
        query="SELECT t2.id AS id, t1.id AS pid, t1.x AS x, t1.y AS y, t1.z AS z, t2.nick AS nick, t2.fakenick AS fakenick, t2.alliance AS alliance, t2.relay AS relay, t2.reportchan AS reportchan, t2.hostile_count AS hostile_count, t2.scanner AS scanner, t2.distwhore AS distwhore, t2.comment AS comment FROM planet_dump as t1, intel as t2 WHERE tick=(SELECT MAX(tick) FROM updates) AND t1.id=t2.pid AND x=%s AND y=%s ORDER BY y,z,x"
        self.cursor.execute(query,(x,y))
        if self.cursor.rowcount < 1:
            self.client.reply(prefix,nick,target,"No information stored for galaxy %s:%s" % (x,y))
            return 1
        for d in self.cursor.dictfetchall():
            x=d['x']
            y=d['y']
            z=d['z']            
            i=loadable.intel(pid=d['pid'],nick=d['nick'],fakenick=d['fakenick'],
                             alliance=d['alliance'],relay=d['relay'],reportchan=d['reportchan'],
                             hostile_count=d['hostile_count'],scanner=d['scanner'],
                             distwhore=d['distwhore'],comment=d['comment'])
            if not i.is_empty():
                reply="Information stored for %s:%s:%s - "% (x,y,z)
                reply+=i.__str__()
                self.client.reply(prefix,nick,target,reply)            
        return 1

