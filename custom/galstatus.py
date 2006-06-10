#import re, os, sys, string, psycopg, loadable, threading, traceback

import re,traceback,loadable

class galstatus:
    def __init__(self, client,conn,cursor):
        self.client=client
        self.conn=conn
        self.cursor=cursor
        self.statusre=re.compile(r"(\d+):(\d+):(\d+)\*?\s+(\d+):(\d+):(\d+)\s+(.*?)\s+((Xan|Ter|Cat|Zik)\s+)?(\d+)\s+(Return|Attack|Defend)\s+(\d+)")

    def parse(self,message,nick,pnick):
        try:
            self.unsafe_method(message,nick,pnick)
        except Exception, e:
            print "Exception in galstatus: "+e.__str__()
            self.client.privmsg('jesterina',"Exception in scan: "+e.__str__())
            traceback.print_exc()

    def unsafe_method(self,message,nick,pnick):
        m=self.statusre.search(message)
        if not m:

            return
        print m.groups()

        target_x=m.group(1)
        target_y=m.group(2)
        target_z=m.group(3)        

        owner_x=m.group(4)
        owner_y=m.group(5)
        owner_z=m.group(6)        



        fleetname=m.group(7)
        race=m.group(9)
        fleetsize=m.group(10)
        mission=m.group(11)
        eta=m.group(12)

        print "%s:%s:%s %s:%s:%s '%s' %s m:%s e:%s"%(owner_x,owner_y,owner_z,target_x,target_y,target_z,fleetname,fleetsize,mission,eta)

        owner=loadable.planet(owner_x,owner_y,owner_z)
        if not owner.load_most_recent(self.conn, 0 ,self.cursor):
            return
        target=loadable.planet(target_x,target_y,target_z)
        if not target.load_most_recent(self.conn, 0 ,self.cursor):
            return

        self.cursor.execute("SELECT max_tick() AS max_tick")
        curtick=self.cursor.dictfetchone()['max_tick']

        query="INSERT INTO fleet(owner,target,fleet_size,fleet_name,landing_tick,mission) VALUES (%s,%s,%s,%s,%s,%s)"

        try:
            self.cursor.execute(query,(owner.id,target.id,fleetsize,fleetname,int(eta)+int(curtick),mission.lower()))
        except Exception,e:
            print "Exception in galstatus: "+e.__str__()
            traceback.print_exc()
