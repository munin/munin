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

# Nothing alliance specific in here as far as I can tell.
# qebab, 24/6/08.

import string

class intel(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,50)
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + " <x:y:z> [option=value]+"
        self.planet_coordre=re.compile(r"(\d+)[. :-](\d+)[. :-](\d+)(.*)")
        self.gal_coordre=re.compile(r"(\d+)[. :-](\d+)")
        # self.optionsre={}
        # self.optionsre['nick']=re.compile("^(\S+)")
        # self.optionsre['gov']=re.compile("^(\S+)")
        # self.optionsre['bg']=re.compile("^(\S+)")
        # self.optionsre['covop']=re.compile("^(t|f)",re.I)
        # self.optionsre['defwhore']=re.compile("^(t|f)",re.I)
        # self.optionsre['fakenick']=re.compile("^(\S+)")
        # self.optionsre['alliance']=re.compile("^(\S+.*?)(\s+\S+)?$")
        # self.optionsre['reportchan']=re.compile("^(\S+)")
        # self.optionsre['relay']=re.compile("^(t|f)",re.I)
        # self.optionsre['scanner']=re.compile("^(t|f)",re.I)
        # self.optionsre['distwhore']=re.compile("^(t|f)",re.I)
        # self.optionsre['comment']=re.compile("^(.*)")                
        # options=self.optionsre.keys()
        # options.sort()
        # self.helptext=["Valid options: %s" % (string.join(options,', '))]
        self.options = ['alliance', 'nick', 'fakenick', 'defwhore', 'covop', 'scanner', 'distwhore', 'bg', 'gov', 'relay', 'reportchan', 'comment']
        self.nulls = ["<>",".","-","?"]
        self.true = ["1","yes","y","true","t"]
        self.false = ["0","no","n","false","f"]
        self.helptext=["Valid options: %s" % (string.join(self.options,', '))]

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
        for opt, val in opts.items():
            if opt == "alliance":
                if val in self.nulls:
                    a=loadable.alliance(id=None)
                    continue
                a=loadable.alliance(name=val)
                if not a.load_most_recent(self.conn,self.client,self.cursor):
                    self.client.reply(prefix,nick,target,"'%s' is not a valid alliance, your information was not added."%(val,))
                    return 1
            if (opt in self.options) and (val in self.nulls):
                opts[opt] = None
                continue
            if opt in ("nick","fakenick","bg","gov","reportchan"):
                opts[opt] = val
            if opt in ("defwhore","covop","scanner","distwhore","relay"):
                if val in self.true:
                    opts[opt] = True
                if val in self.false:
                    opts[opt] = False
            if opt == "comment":
                opts[opt] = command.split("comment=")[1]

        for k in self.optionsre.keys():
            if not opts.has_key(k):
                opts[k]=getattr(i,k)
        # if opts['alliance']:
            # a=loadable.alliance(name=opts['alliance'])
            # if not a.load_most_recent(self.conn,self.client,self.cursor):
                # if opts['alliance'] in self.nulls:
                    # a.id=None
                # else:
                    # self.client.reply(prefix,nick,target,"'%s' is not a valid alliance, your information was not added."%(opts['alliance'],))
                    # return 1
        # else:
            # a=loadable.alliance(id=None)

        if i.id:
            query="UPDATE intel SET "
            query+="pid=%s,nick=%s,fakenick=%s,defwhore=%s,gov=%s,bg=%s,covop=%s,alliance_id=%s,relay=%s,reportchan=%s,"
            query+="scanner=%s,distwhore=%s,comment=%s"
            query+=" WHERE id=%s"
            self.cursor.execute(query,(opts['pid'],opts['nick'],
                                       opts['fakenick'],opts['defwhore'],opts['gov'],opts['bg'],
                                       opts['covop'],a.id,opts['relay'],opts['reportchan'],
                                       opts['scanner'],opts['distwhore'],opts['comment'],i.id))
        elif params:
            query="INSERT INTO intel (pid,nick,fakenick,defwhore,gov,bg,covop,relay,reportchan,scanner,distwhore,comment,alliance_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            self.cursor.execute(query,(opts['pid'],opts['nick'],
                                       opts['fakenick'],opts['defwhore'],opts['gov'],opts['bg'],
                                       opts['covop'],opts['relay'],opts['reportchan'],
                                       opts['scanner'],opts['distwhore'],
                                       opts['comment'],a.id))
        i=loadable.intel(pid=opts['pid'],nick=opts['nick'],fakenick=opts['fakenick'],defwhore=opts['defwhore'],gov=opts['gov'],bg=opts['bg'],
                         covop=opts['covop'],alliance=opts['alliance'],relay=opts['relay'],reportchan=opts['reportchan'],
                         scanner=opts['scanner'],distwhore=opts['distwhore'],comment=opts['comment'])

        reply="Information stored for %s:%s:%s - "% (p.x,p.y,p.z)
        reply+=i.__str__()
        self.client.reply(prefix,nick,target,reply)
        
        return 1

    # def split_opts(self,params):
        # param_dict={}
        # active_opt=None
        # for s in params.split('='):
            # if active_opt:
                # m=self.optionsre[active_opt].search(s)
                # if m:
                    # param_dict[active_opt]=m.group(1)
            # last_act=active_opt
            # for key in self.optionsre.keys():
                # if s.endswith(" "+key):
                    # active_opt=key
            # if active_opt == last_act:
                # active_opt=None
        # return param_dict
    
    def split_opts(self,params):
        param_dict={}
        for s in params.split():
            a=s.split('=')
            if len(a) != 2:
                continue
            param_dict[a[0].lower()]=a[1]
        return param_dict
#    def help(self):



    def exec_gal(self,nick,username,host,target,prefix,command,user,access,x,y):
        query="SELECT t2.id AS id, t1.id AS pid, t1.x AS x, t1.y AS y, t1.z AS z, t2.nick AS nick, t2.fakenick AS fakenick, t2.defwhore AS defwhore, t2.gov AS gov, t2.bg AS bg, t2.covop AS covop, t2.alliance_id AS alliance_id, t2.relay AS relay, t2.reportchan AS reportchan, t2.scanner AS scanner, t2.distwhore AS distwhore, t2.comment AS comment, t3.name AS alliance FROM planet_dump as t1, intel as t2 LEFT JOIN alliance_canon AS t3 ON t2.alliance_id=t3.id WHERE tick=(SELECT MAX(tick) FROM updates) AND t1.id=t2.pid AND x=%s AND y=%s ORDER BY y,z,x"
        self.cursor.execute(query,(x,y))

        replied_to_request = False
        for d in self.cursor.dictfetchall():
            x=d['x']
            y=d['y']
            z=d['z']            
            i=loadable.intel(pid=d['pid'],nick=d['nick'],fakenick=d['fakenick'],defwhore=d['defwhore'],gov=d['gov'],bg=d['bg'],
                             covop=d['covop'],alliance=d['alliance'],relay=d['relay'],reportchan=d['reportchan'],
                             scanner=d['scanner'],distwhore=d['distwhore'],comment=d['comment'])
            if not i.is_empty():
                replied_to_request = True
                reply="Information stored for %s:%s:%s - "% (x,y,z)
                reply+=i.__str__()
                self.client.reply(prefix,nick,target,reply)

        if not replied_to_request:
            self.client.reply(prefix,nick,target,"No information stored for galaxy %s:%s" % (x,y))
        return 1
