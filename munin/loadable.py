"""
Loadable class
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

import re
import string
import ConfigParser
import psycopg
from mx import DateTime

class loadable(object):
    def __init__(self,cursor,level):
        self.cursor=cursor
        self.level=level
        self.coordre=re.compile(r"(\d+)[. :-](\d+)([. :-](\d+))?")
        self.planet_coordre=re.compile(r"(\d+)[. :-](\d+)[. :-](\d+)")
        self.idre=re.compile(r"([0-9a-zA-Z]+)")
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)",re.I)
        self.helptext=None
        self.config = ConfigParser.ConfigParser()
        if not self.config.read('muninrc'):
            raise ValueError('Failed to read ./muninrc. Can not run without configuration')

    def execute(self,user,access,irc_msg):
        print "Loadable execute"
        pass

    def help(self,user,access,irc_msg):
        irc_msg.reply(self.usage)
        if self.helptext:
            for h in self.helptext:
                irc_msg.reply(h)

    def cap(self,text):
        if len(text)>3:
            return text.title()
        else:
            return text.upper()

    def format_value(self,cost):
        value=cost/100
        if value/1000000 > 9:
            return str(value/1000000)+"m"
        elif value/1000 > 9:
            return str(value/1000)+"k"
        else:
            return str(value)

    def format_real_value(self,value):
        return self.format_value(value*100)

    def split_opts(self,params):
        param_dict={}
        for s in params.split():
            a=s.split('=')
            if len(a) != 2:
                return None
            param_dict[a[0].lower()]=a[1]
        return param_dict

    def current_tick(self):
        self.cursor.execute("SELECT MAX(tick) FROM updates")
        return self.cursor.fetchone()[0]

    def load_user(self,pnick,irc_msg):
        if not pnick:
            irc_msg.reply("You must be registered to use the "+self.__class__.__name__+" command (log in with P and set mode +x)")
            return None
        u=self.load_user_from_pnick(pnick)
        if not u:
            irc_msg.reply("You must be registered to use the automatic "+self.__class__.__name__+" command (log in with P and set mode +x, then make sure you've set your planet with the pref command)")
            return None
        return u

    def load_user_from_pnick(self,username):
        u=user(pnick=username)
        if u.load_from_db(self.cursor):
            return u
        else:
            return None

    def pluralize(self,number,text):
        if text.lower() == "cookie" and number != 1:
            return text+"s"
        elif text.lower() == "carebear" and number != 1:
            return text+"s"
        elif text.lower() == "day" and number != 1:
            return text+"s"
        return text

    def match_or_usage(self, irc_msg, needle, haystack):
        m=needle.search(haystack)
        if not m:
            irc_msg.reply("Usage: %s" %(self.usage,))
        return m
    def command_not_used_in_home(self,irc_msg,command_name):
        if irc_msg.target.lower() != "#"+self.config.get("Auth","home").lower():
            irc_msg.reply("The %s command may only be used in #%s."%(command_name,self.config.get("Auth","home"),))
            return True
        False

    def phone_query_builder(self,u,query_filter=None,query_args=None):
        args=(u.id,)
        query="SELECT pnick "
        query+=" FROM phone AS t1"
        query+=" INNER JOIN user_list AS t2"
        query+=" ON t2.id=t1.user_id"
        query+=" WHERE t1.user_id=%s"
        if query_filter:
            query+=query_filter
            args+=query_args

        self.cursor.execute(query,args)
        return self.cursor.dictfetchall()

class defcall(object):
    def __init__(self,id=-1,bcalc=None,status=-1,claimed_by=None,comment=None,target=None,landing_tick=-1):
        self.id=id
        self.bcalc=bcalc
        self.status=status
        self.claimed_by=claimed_by
        self.comment=comment
        self.target=target
        self.landing_tick=landing_tick
        self.actual_target=None
        self.actual_owner=None
        self.actual_status=None
        pass

    def __str__(self):
        ret_str="Defcall with id %s for %s:%s:%s landing %s"%(self.id,self.actual_target.x,self.actual_target.y,self.actual_target.z,self.landing_tick)
        ret_str+=" has status '%s' and was last modified by %s."%(self.actual_status,self.claimed_by or "no one")
        ret_str+=" It has"
        if self.bcalc:
            ret_str+=" a"
        else:
            ret_str+=" no"
        ret_str+=" bcalc and has"
        if self.comment:
            ret_str+=" a"
        else:
            ret_str+=" no"
        ret_str+=" comment."
        return ret_str

    def load_most_recent(self,cursor):
        #for now, always load from ID
        query="SELECT id,bcalc,status,claimed_by,comment,target,landing_tick"
        query+=" FROM defcalls WHERE id=%s"
        args=(self.id,)
        cursor.execute(query,args)
        d=cursor.dictfetchone()
        if not d:
            return 0
        self.bcalc=d['bcalc']
        self.status=d['status']
        self.claimed_by=d['claimed_by']
        self.comment=d['comment']
        self.target=d['target']
        self.landing_tick=d['landing_tick']
        p=planet(id=self.target)
        if not p.load_most_recent(cursor):
            raise Exception("Defcall with id %s has no valid planet information. Oops...")
        self.actual_target=p

        u=user(id=self.claimed_by)
        if not u.load_from_db(cursor):
            self.actual_owner=None
        self.actual_owner=u

        query="SELECT status FROM defcall_status WHERE id = %s"
        cursor.execute(query,(self.status,))
        s=cursor.dictfetchone()
        if not s:
            irc_msg.reply("foo!")
        self.actual_status=s['status']

        return 1

class fleet(object):
    def __init__(self,id=-1,scan_id=-1,owner_id=-1,target_id=None,fleet_size=-1,fleet_name=None,launch_tick=-1,landing_tick=-1,mission=None,defcall=None):
        self.id=id
        self.scan_id=scan_id
        self.owner_id=owner_id
        self.target_id=target_id
        self.fleet_size=fleet_size
        self.fleet_name=fleet_name
        self.launch_tick=launch_tick
        self.landing_tick=landing_tick
        self.mission=mission
        self.defcall=defcall
        self.actual_target=None
        self.actual_owner=None
        self.actual_rand_id=None
        self.eta=-1
        pass

    def __str__(self):
        reply="Fleet with id: %s from %s:%s:%s (%s)"%(self.id,self.actual_owner.x,
                                                      self.actual_owner.y,self.actual_owner.z,
                                                      self.actual_owner.race)
        reply+=" named '%s' with %s ships" %(self.fleet_name,self.fleet_size)
        reply+=" headed for %s:%s:%s"%(self.actual_target.x,self.actual_target.y,self.actual_target.z)

        reply+=" with eta %s"%(self.eta,)
        if self.launch_tick:
            reply+=" (%s)"%(self.landing_tick-self.launch_tick,)
        reply+=" and mission %s"%(self.mission,)
        if self.defcall:
            reply+=" as part of defcall id: %s"%(self.defcall.id,)
        return reply


    def load_most_recent(self,cursor):
        #for now, always load from ID
        query="SELECT id,scan_id,owner_id,target,fleet_size,fleet_name"
        query+=",launch_tick,landing_tick, (landing_tick-(SELECT max_tick())) AS eta,mission"
        query+=" FROM fleet WHERE id=%s"
        args=(self.id,)
        cursor.execute(query,args)
        d=cursor.dictfetchone()
        if not d:
            return 0
        self.id=d['id']
        self.scan_id=d['scan_id']
        self.owner_id=d['owner_id']
        self.target_id=d['target']
        self.fleet_size=d['fleet_size']
        self.fleet_name=d['fleet_name']
        self.launch_tick=d['launch_tick']
        self.landing_tick=d['landing_tick']
        self.mission=d['mission']
        self.eta=d['eta']

        p=planet(id=self.target_id)
        if not p.load_most_recent(cursor):
            raise Exception("Defcall with id %s has no valid target information. Oops..."%(self.id,))
        self.actual_target=p

        p=planet(id=self.owner_id)
        if not p.load_most_recent(cursor):
            raise Exception("Defcall with id %s has no valid owner information. Oops..."%(self.id,))
        self.actual_owner=p

        query="SELECT rand_id FROM scan WHERE id = %s"
        cursor.execute(query,(self.scan_id,))
        s=cursor.dictfetchone()
        if s:
            self.actual_rand_id=s['rand_id']

        query="SELECT id FROM defcalls WHERE target=%s AND landing_tick=%s"
        cursor.execute(query,(self.target_id,self.landing_tick))
        s=cursor.dictfetchone()
        if s:
            defc=defcall(id=s['id'])
            if defc.load_most_recent(cursor):
                self.defcall=defc
        return 1


class planet(object):
    def __init__(self,x=-1,y=-1,z=-1,planetname=None,rulername=None,race=None,size=-1,score=-1,value=-1,id=-1,idle=-1):
        self.x=int(x)
        self.y=int(y)
        self.z=int(z)
        self.rulername=rulername
        self.planetname=planetname
        self.race=race
        self.size=int(size)
        self.score=int(score)
        self.value=int(value)
        self.score_rank=-1
        self.value_rank=-1
        self.size_rank=-1
        self.xp=-1
        self.xp_rank=-1
        self.id=id
        self.idle=idle

    def __str__(self):
        retstr="%s:%s:%s (%s) '%s' of '%s' " % (self.x,self.y,self.z,self.race,self.rulername,self.planetname)
        retstr+="Score: %s (%s) " % (self.score,self.score_rank)
        retstr+="Value: %s (%s) " % (self.value,self.value_rank)
        retstr+="Size: %s (%s) " % (self.size,self.size_rank)
        retstr+="XP: %s (%s) " % (self.xp,self.xp_rank)
        retstr+="Idle: %s " % (self.idle,)
        return retstr
        pass

    def load_most_recent(self,cursor):
        p={}
        if self.x > -1 and self.y > -1 and self.z > -1:
            #load from coords
            query="SELECT x,y,z,planetname,rulername,race,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,idle,id FROM planet_dump WHERE x=%s AND y=%s AND z=%s AND tick=(SELECT MAX(tick) FROM updates)"
            cursor.execute(query,(self.x,self.y,self.z))
            pass
        elif self.planetname and self.rulername:
            query="SELECT x,y,z,planetname,rulername,race,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,idle,id FROM planet_dump WHERE planetname=%s AND rulername=%s AND tick=(SELECT MAX(tick) FROM updates)"
            cursor.execute(query,(self.planetname,self.rulername))
            pass
        elif self.id > 0:
            query="SELECT x,y,z,planetname,rulername,race,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,idle,id FROM planet_dump WHERE id=%s AND tick=(SELECT MAX(tick) FROM updates)"
            cursor.execute(query,(self.id,))
        else:
            raise Exception("Tried to load planet with no unique identifiers")
        p=cursor.dictfetchone()
        if not p:
            return None
        self.x=p['x']
        self.y=p['y']
        self.z=p['z']
        self.rulername=p['rulername']
        self.planetname=p['planetname']
        self.race=p['race']
        self.size=p['size']
        self.score=p['score']
        self.value=p['value']
        self.score_rank=p['score_rank']
        self.value_rank=p['value_rank']
        self.size_rank=p['size_rank']
        self.xp=p['xp']
        self.xp_rank=p['xp_rank']
        self.idle=p['idle']
        self.id=p['id']
        return 1

    def calc_xp(self,victim):
        bravery = max(0,(min(2,float(victim.value)/self.value)-0.1 ) * (min(2,float(victim.score)/self.score)-0.2))
        bravery *= 10
        return int(bravery*int(victim.size*0.25))



class galaxy(object):
    def __init__(self,x=-1,y=-1,name=None,size=-1,score=-1,value=-1,id=-1):
        self.x=int(x)
        self.y=int(y)
        self.name=name
        self.size=int(size)
        self.score=int(score)
        self.value=int(value)
        self.score_rank=-1
        self.value_rank=-1
        self.size_rank=-1
        self.xp=-1
        self.xp_rank=-1
#        self.score_avg=-1
#        self.size_avg=-1
#        self.value_avg=-1
#        self.xp_avg=-1
        self.id=id
        self.members=-1


    def __str__(self):
        retstr="%s:%s '%s' " % (self.x,self.y,self.name)
        retstr+="Score: %s (%s) " % (self.score,self.score_rank)
        retstr+="Value: %s (%s) " % (self.value,self.value_rank)
        retstr+="Size: %s (%s) " % (self.size,self.size_rank)
        retstr+="XP: %s (%s) " % (self.xp,self.xp_rank)
        return retstr
        pass

    def load_most_recent(self,cursor):
        g={}
        if self.x > 0 and self.y > 0:
            #load from coords
            query="SELECT x,y,name,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,id FROM galaxy_dump WHERE x=%s AND y=%s AND tick=(SELECT MAX(tick) FROM updates)"
            cursor.execute(query,(self.x,self.y))
            pass
        else:
            raise Exception("Tried to load planet with no unique identifiers")
        g=cursor.dictfetchone()
        if not g:
            return None
        self.x=g['x']
        self.y=g['y']
        self.name=g['name']
        self.size=g['size']
        self.score=g['score']
        self.value=g['value']
        self.score_rank=g['score_rank']
        self.value_rank=g['value_rank']
        self.size_rank=g['size_rank']
        self.xp=g['xp']
        self.xp_rank=g['xp_rank']
        self.id=g['id']
        return 1


class alliance(object):
    def __init__(self,score_rank=-1,name=None,size=-1,members=-1,score=-1,id=None):
        self.score_rank=int(score_rank)
        self.name=name
        self.size=int(size)
        self.members=int(members)
        self.score=int(score)
        self.size_rank=-1
        self.members_rank=-1
        self.score_avg=-1
        self.size_avg=-1
        self.score_avg_rank=-1
        self.size_avg_rank=-1

        self.id=id

    def __str__(self):
        retstr="'%s' Members: %s (%s) " % (self.name,self.members,self.members_rank)
        retstr+="Score: %s (%s) Avg: %s (%s) " % (self.score,self.score_rank,self.score_avg,self.score_avg_rank)
        retstr+="Size: %s (%s) Avg: %s (%s)" % (self.size,self.size_rank,self.size_avg,self.size_avg_rank)
        return retstr
        pass

    def load_most_recent(self,cursor):
        a={}
        if self.name:
            #load from exact name
            query="SELECT name,size,members,score,size_rank,members_rank,score_rank,score_avg,size_avg,score_avg_rank,size_avg_rank,id FROM alliance_dump WHERE name ILIKE %s AND tick=(SELECT MAX(tick) FROM updates)"
            cursor.execute(query,(self.name,))

            #if that doesn't work, load from fuzzy name
            if cursor.rowcount < 1:
                query="SELECT name,size,members,score,size_rank,members_rank,score_rank,score_avg,size_avg,score_avg_rank,size_avg_rank,id FROM alliance_dump WHERE name ILIKE %s AND tick=(SELECT MAX(tick) FROM updates)"
                cursor.execute(query,("%"+self.name+"%",))
            pass
        else:
            raise Exception("Tried to load planet with no unique identifiers")
        a=cursor.dictfetchone()
        if not a:
            return None
        self.name=a['name']
        self.size=a['size']
        self.score=a['score']
        self.score_rank=a['score_rank']
        self.size_rank=a['size_rank']
        self.members=a['members']
        self.members_rank=a['members_rank']
        self.score_avg=a['score_avg']
        self.size_avg=a['size_avg']
        self.score_avg_rank=a['score_avg_rank']
        self.size_avg_rank=a['size_avg_rank']
        self.id=a['id']
        return 1

class user(object):
    def __init__(self,id=-1,pnick=None,sponsor=None,userlevel=-1,planet_id=-1,phone=None,pubphone=False,stay=False,invites=-1,available_cookies=-1,last_cookie_date=None,carebears=-1):
        self.id=id
        self.pnick=pnick
        self.sponsor=sponsor
        self.userlevel=userlevel
        self.planet_id=planet_id
        self.planet=None
        self.phone=phone
        self.pubphone=pubphone
        self.stay=stay
        self.pref=False
        self.available_cookies=-1
        self.last_cookie_date=None
        self.invites=-1
        self.carebears=carebears

    def lookup_query(self):
        query="SELECT t1.id AS id, t1.pnick AS pnick, t1.sponsor AS sponsor, t1.userlevel AS userlevel, t1.planet_id AS planet_id, t1.phone AS phone, t1.pubphone AS pubphone,"
        query+=" t1.stay AS stay, t1.invites AS invites, t1.available_cookies AS available_cookies, t1.last_cookie_date AS last_cookie_date, t1.carebears AS carebears "
        query+=" FROM user_list AS t1 WHERE"
        return query

    def load_from_db(self,cursor):
        query=self.lookup_query()
        if self.pnick:
            query+=" t1.pnick ILIKE %s"
            cursor.execute(query,(self.pnick,))
        elif self.id > 0:
            query+=" t1.id=%s"
            cursor.execute(query,(self.id,))
        else:
            return None
        u=cursor.dictfetchone()
        if not u and self.pnick:
            query=self.lookup_query()
            query+=" t1.pnick ILIKE %s"
            query+=" ORDER BY userlevel DESC"
            cursor.execute(query,('%'+self.pnick+'%',))
            u=cursor.dictfetchone()
        if u:
            self.id=u['id']
            self.pnick=u['pnick']
            self.sponsor=u['sponsor']
            self.userlevel=u['userlevel']
            self.planet_id=u['planet_id']
            self.phone=u['phone']
            self.pubphone=u['pubphone']
            if u['planet_id']:
                self.planet=planet(id=self.planet_id)
                self.planet.load_most_recent(cursor)
            else:
                self.planet=None
            self.stay=u['stay']
            self.pref=True
            self.invites=u['invites']
            self.available_cookies=u['available_cookies']
            self.last_cookie_date=u['last_cookie_date']
            self.carebears=u['carebears']
            return 1
        return None

    def munin_number(self,cursor,config):
        if self.sponsor.lower() == config.get("Connection","nick").lower():
            return 1
        u=user(pnick=self.sponsor)
        if u.load_from_db(cursor) and u.userlevel >= 100 and u.pnick.lower() != u.sponsor.lower():
            parent_number = u.munin_number(cursor,config )
            if parent_number:
                return parent_number + 1
            else:
                parent_number
        else:
            return None # dead subtree, get rid of these.

    def check_available_cookies(self,cursor,config):
        now = DateTime.now()
        if not self.last_cookie_date or DateTime.Age(now,self.last_cookie_date).days > 6:
            self.available_cookies = int(config.get("Alliance","cookies_per_week"))
            query="UPDATE user_list SET available_cookies = %s,last_cookie_date = %s WHERE id = %s"
            last_monday=now - DateTime.RelativeDateTime(days=(now.day_of_week))
            cursor.execute(query,(self.available_cookies,psycopg.TimestampFromMx(last_monday), self.id))

        return self.available_cookies
    
class intel(object):
    def __init__(self,id=None,pid=-1,nick=None,gov=None,bg=None,covop=False,defwhore=False,fakenick=None,alliance=None,reportchan=None,scanner=False,distwhore=False,relay=False,comment=None):
        self.id=id
        self.pid=pid
        self.nick=nick
        self.gov=gov
        self.covop=covop
        self.bg=bg
        self.defwhore=defwhore
        self.fakenick=fakenick
        self.alliance=alliance
        self.reportchan=reportchan
        self.relay=relay
        self.scanner=scanner
        self.distwhore=distwhore
        self.comment=comment

    def load_from_db(self,cursor):
        query="SELECT t2.id AS id,pid,nick,defwhore,gov,covop,bg,fakenick,relay,reportchan,scanner,distwhore,comment,t1.name AS alliance"
        query+=" FROM intel AS t2"
        query+=" LEFT JOIN alliance_canon AS t1 ON t2.alliance_id=t1.id "
        query+=" WHERE "
        if self.id > 0:
            query+="id=%s"
            cursor.execute(query,(self.id,))
        if self.pid > 0:
            query+="pid=%s"
            cursor.execute(query,(self.pid,))

        elif self.nick:
            query+="nick=%s LIMIT 1"
            cursor.execute(query,("%"+self.nick+"%",))
        elif self.fakenick:
            query+="fakenick=%s LIMIT 1"
            cursor.execute(query,("%"+self.fakenick+"%",))
        elif self.comment:
            query+="comment=%s LIMIT 1"
            cursor.execute(query,("%"+self.comment+"%",))
        i=cursor.dictfetchone()
        if not i:
            return None
        self.id=i['id']
        self.pid=i['pid']
        self.nick=i['nick']
        self.gov=i['gov']
        self.defwhore=i['defwhore'] and True or False
        self.bg=i['bg']
        self.covop=i['covop'] and True or False
        self.fakenick=i['fakenick']
        self.alliance=i['alliance']
        self.reportchan=i['reportchan']
        self.relay=i['relay'] and True or False
        self.scanner=bool(i['scanner']) and True or False
        self.distwhore=bool(i['distwhore']) and True or False
        self.comment=i['comment']
        print i
        return 1

    def __str__(self):
        retlist=[]
        if self.nick:
            retlist.append("nick=%s"%(self.nick,))
        if self.fakenick:
            retlist.append("fakenick=%s"%(self.fakenick,))
        if self.gov:
            retlist.append("gov=%s"%(self.gov,))
        if self.defwhore:
            retlist.append("defwhore=%s"%(self.defwhore,))
        if self.bg:
            retlist.append("bg=%s"%(self.bg,))
        if self.covop:
            retlist.append("covop=%s"%(self.covop,))
        if self.alliance:
            retlist.append("alliance=%s"%(self.alliance,))
        if self.relay:
            retlist.append("relay=%s"%(self.relay,))
        if self.reportchan:
            retlist.append("reportchan=%s"%(self.reportchan,))
        if self.scanner:
            retlist.append("scanner=%s"%(self.scanner,))
        if self.distwhore:
            retlist.append("distwhore=%s"%(self.distwhore,))
        if self.comment:
            retlist.append("comment=%s"%(self.comment,))


        return string.join(retlist)

    def change_list(self):
        retlist=[]
        if self.nick:
            retlist.append("nick=%s")
        if self.fakenick:
            retlist.append("fakenick=%s")
        if self.gov:
            retlist.append("gov=%s")
        if self.defwhore:
            retlist.append("defwhore=%s")
        if self.bg:
            retlist.append("bg=%s")
        if self.covop:
            retlist.append("covop=%s")
        if self.alliance:
            retlist.append("alliance=%s")
        if self.relay:
            retlist.append("relay=%s")
        if self.reportchan:
            retlist.append("reportchan=%s")
        if self.scanner:
            retlist.append("scanner=%s")
        if self.distwhore:
            retlist.append("distwhore=%s")
        if self.comment:
            retlist.append("comment=%s")

        return string.join(retlist)

    def change_tuple(self):
        rettup=()
        if self.nick:
            rettup+=(self.nick,)
        if self.fakenick:
            rettup+=(self.fakenick,)
        if self.gov:
            rettup+=(self.gov,)
        if self.defwhore:
            rettup+=(self.defwhore,)
        if self.bg:
            rettup+=(self.bg,)
        if self.covop:
            rettup+=(self.covop,)
        if self.alliance:
            rettup+=(self.alliance,)
        if self.relay:
            rettup+=(self.relay,)
        if self.reportchan:
            rettup+=(self.reportchan,)
        if self.scanner:
            rettup+=(self.scanner,)
        if self.distwhore:
            rettup+=(self.distwhore,)
        if self.comment:
            rettup+=(self.comment,)

        return rettup

    def is_empty(self):

        if self.nick:
            return 0
        if self.fakenick:
            return 0
        if self.bg:
            return 0
        if self.defwhore:
            return 0
        if self.gov:
            return 0
        if self.covop:
            return 0
        if self.alliance:
            return 0
        if self.relay:
            return 0
        if self.reportchan:
            return 0
        if self.scanner:
            return 0
        if self.distwhore:
            return 0
        if self.comment:
            return 0
        return 1



class booking(object):
    def __init__(self,id=-1,pnick=None,nick=None,tick=-1,pid=-1,uid=-1):
        self.id=id
        self.pnick=pnick
        self.nick=nick
        self.tick=tick
        self.pid=pid
        self.uid=uid

    def load_from_db(self,cursor):
        query="SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid FROM target AS t1 WHERE "

        if tick and pid:
            query+="pid=%s AND tick=%s "
            cursor.execute(query,(self.pnick,))
            b=cursor.dictfetchone()
            if not b:
                return None
            self.id=b['id']
            self.pnick=b['pnick']
            self.nick=b['nick']
            self.tick=b['tick']
            self.pid=b['pid']
            self.uid=b['uid']
            return 1
        else:
            return None
        return None
