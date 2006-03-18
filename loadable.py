"""
Loadable class
"""
import re,string

class loadable:
    def __init__(self,client,conn,cursor,level):
        self.client=client
        self.conn=conn
        self.cursor=cursor
        self.level=level
        self.coordre=re.compile(r"(\d+)[. :-](\d+)([. :-](\d+))?")
        self.planet_coordre=re.compile(r"(\d+)[. :-](\d+)[. :-](\d+)")
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)",re.I)
        pass

    def execute(self,nick,username,host,target,prefix,command,user,access):
        print "Loadable execute"
        pass

    def help(self):
        return self.usage

    def format_value(self,cost):
        value=cost/100
        if value/1000000 > 9:
            return str(value/1000000)+"m"
        elif value/1000 > 9:
            return str(value/1000)+"k"        
        else:
            return str(value)

    def split_opts(self,params):
        param_dict={}
        for s in params.split():
            a=s.split('=')
            if len(a) != 2:
                return None
            param_dict[a[0].lower()]=a[1].lower()
        return param_dict

    def current_tick(self):
        self.cursor.execute("SELECT MAX(tick) FROM updates")
        return self.cursor.fetchone()[0]
        

class planet:
    def __init__(self,x=-1,y=-1,z=-1,planetname=None,rulername=None,race=None,size=-1,score=-1,value=-1,id=-1):
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

    def __str__(self):
        retstr="%s:%s:%s (%s) '%s' of '%s' " % (self.x,self.y,self.z,self.race,self.rulername,self.planetname)
        retstr+="Score: %s (%s) " % (self.score,self.score_rank)
        retstr+="Value: %s (%s) " % (self.value,self.value_rank)
        retstr+="Size: %s (%s) " % (self.size,self.size_rank)
        retstr+="XP: %s (%s) " % (self.xp,self.xp_rank)
        return retstr
        pass
    
    def load_most_recent(self,conn,client,cursor):
        p={}
        if self.x > -1 and self.y > -1 and self.z > -1:
            #load from coords
            query="SELECT x,y,z,planetname,rulername,race,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,id FROM planet_dump WHERE x=%s AND y=%s AND z=%s AND tick=(SELECT MAX(tick) FROM updates)"
            cursor.execute(query,(self.x,self.y,self.z))
            pass
        elif self.planetname and self.rulername:
            query="SELECT x,y,z,planetname,rulername,race,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,id FROM planet_dump WHERE planetname=%s AND rulername=%s AND tick=(SELECT MAX(tick) FROM updates)"
            cursor.execute(query,(self.planetname,self.rulername))
            pass
        elif self.id > 0:
            query="SELECT x,y,z,planetname,rulername,race,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,id FROM planet_dump WHERE id=%s AND tick=(SELECT MAX(tick) FROM updates)"
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
        self.id=p['id']
        return 1
    
class galaxy:
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
    
    def load_most_recent(self,conn,client,cursor):
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


class alliance:
    def __init__(self,score_rank=-1,name=None,size=-1,members=-1,score=-1,id=-1):
        self.score_rank=int(score_rank)
        self.name=name
        self.size=int(size)
        self.members=int(members)
        self.score=int(score)
        self.size_rank=-1
        self.members_rank=-1
        self.score_avg=-1
        self.size_avg=-1
        self.id=id
        
    def __str__(self):
        retstr="'%s' Members: %s (%s) " % (self.name,self.members,self.members_rank)
        retstr+="Score: %s (%s) Avg: %s " % (self.score,self.score_rank,self.score_avg)
        retstr+="Size: %s (%s) Avg: %s " % (self.size,self.size_rank,self.size_avg)
        return retstr
        pass

    def load_most_recent(self,conn,client,cursor):
        a={}
        if self.name:
            #load from fuzzy name
            query="SELECT name,size,members,score,size_rank,members_rank,score_rank,score_avg,size_avg,id FROM alliance_dump WHERE name ILIKE %s AND tick=(SELECT MAX(tick) FROM updates)"
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
        self.id=a['id']
        return 1    

class user:
    def __init__(self,id=-1,pnick=None,userlevel=-1,planet_id=-1,stay=False):
        self.id=id
        self.pnick=pnick
        self.userlevel=userlevel
        self.planet_id=planet_id
        self.planet=None
        self.stay=False
        self.pref=False
#        if planet_id > 0:
#            self.planet=planet(id=planet_id)
#        else:
#            self.planet=None
        

    def load_from_db(self,conn,client,cursor):
        if self.pnick:
            query="SELECT t1.id AS id, t1.pnick AS pnick, t1.userlevel AS userlevel, t2.planet_id AS planet_id, t2.stay AS stay FROM user_list AS t1, user_pref AS t2 WHERE t2.id=t1.id AND t1.pnick ILIKE %s"
            cursor.execute(query,(self.pnick,))
        elif self.id > 0:
            query="SELECT t1.id AS id, t1.pnick AS pnick, t1.userlevel AS userlevel, t2.planet_id AS planet_id, t2.stay AS stay FROM user_list AS t1, user_pref AS t2 WHERE t2.id=t1.id AND t1.id=%s"
            cursor.execute(query,(self.pnick,))            
        u=cursor.dictfetchone()
        if u:
            self.id=u['id']
            self.pnick=u['pnick']
            self.userlevel=u['userlevel']
            self.planet_id=u['planet_id']
            self.planet=planet(id=self.planet_id)
            self.planet.load_most_recent(conn,client,cursor)
            self.stay=u['stay']
            self.pref=True
            return 1
        else:
            query="SELECT t1.id AS id, t1.pnick AS pnick, t1.userlevel AS userlevel FROM user_list AS t1 WHERE t1.pnick ILIKE %s"
            cursor.execute(query,(self.pnick,))
            u=cursor.dictfetchone()
            if u:
                self.id=u['id']
                self.pnick=u['pnick']
                self.userlevel=u['userlevel']
                return 1
        return None
            

class intel:
    def __init__(self,id=-1,pid=-1,nick=None,fakenick=None,alliance=None,reportchan=None,hostile_count=-1,scanner=False,distwhore=False,comment=None):
        self.id=id
        self.pid=pid        
        self.nick=nick
        self.fakenick=fakenick
        self.alliance=alliance
        self.reportchan=reportchan
        self.hostile_count=hostile_count
        self.scanner=scanner
        self.distwhore=distwhore
        self.comment=comment

    def load_from_db(self,conn,client,cursor):
        query="SELECT id,pid,nick,fakenick,alliance,reportchan,hostile_count,scanner,distwhore,comment FROM intel WHERE "
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
        self.fakenick=i['fakenick']
        self.alliance=i['alliance']
        self.reportchan=i['reportchan']
        self.hostile_count=i['hostile_count']
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
        if self.alliance:
            retlist.append("alliance=%s"%(self.alliance,))
        if self.reportchan:
            retlist.append("reportchan=%s"%(self.reportchan,))                        
        if self.hostile_count > 0:
            retlist.append("hostile_count=%s"%(self.hostile_count,))                        
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
        if self.alliance:
            retlist.append("alliance=%s")
        if self.reportchan:
            retlist.append("reportchan=%s")                        
        if self.hostile_count > 0:
            retlist.append("hostile_count=%s")                        
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
        if self.alliance:
            rettup+=(self.alliance,)
        if self.reportchan:
            rettup+=(self.reportchan,)
        if self.hostile_count > 0:
            rettup+=(self.hostile_count,)
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
        if self.alliance:
            return 0
        if self.reportchan:
            return 0
        if self.hostile_count > 0:
            return 0 
        if self.scanner:
            return 0 
        if self.distwhore:
            return 0
        if self.comment:
            return 0
        return 1



class booking:
    def __init__(self,id=-1,pnick=None,nick=None,tick=-1,pid=-1,uid=-1):
        self.id=id
        self.pnick=pnick
        self.nick=nick
        self.tick=tick
        self.pid=pid
        self.uid=uid

    def load_from_db(self,conn,client,cursor):
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


