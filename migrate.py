#!/usr/bin/python

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

import sys

from psycopg2 import psycopg1 as psycopg

user="munin"

try:
    old_db=sys.argv[1]
    new_db=sys.argv[2]
except:
    print "Usage: %s <old_db> <new_db>" % (sys.argv[0])
    sys.exit(0)


old_conn=psycopg.connect("user=%s dbname=%s" %(user,old_db))
new_conn=psycopg.connect("user=%s dbname=%s" %(user,new_db))

old_curs=old_conn.cursor()

new_curs=new_conn.cursor()

old_curs.execute("SELECT t1.id AS id, t1.pnick AS pnick,t1.userlevel AS userlevel,t1.sponsor AS sponsor, t1.invites AS invites, t1.phone AS phone, t1.pubphone AS pubphone, t1.passwd AS passwd, t1.salt AS salt  FROM user_list AS t1")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO user_list (id,pnick,userlevel,sponsor,invites,phone,pubphone,passwd,salt) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(u['id'],u['pnick'],u['userlevel'],u['sponsor'],u['invites'],u['phone'],['Y','N'][int(u['pubphone'])],u['passwd'],u['salt']))

old_curs.execute("SELECT t1.quote AS quote FROM quote AS t1")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO quote (quote) VALUES (%s)",(u['quote'],))

old_curs.execute("SELECT t1.slogan AS slogan FROM slogan AS t1")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO slogan (slogan) VALUES (%s)",(u['slogan'],))

old_curs.execute("SELECT t1.sponsor_id AS sponsor_id, t1.pnick AS pnick, t1.comment AS comment, t1.timestamp AS timestamp FROM sponsor AS t1");

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO sponsor (sponsor_id,pnick,comment,timestamp) VALUES (%s,%s,%s,%s)",(u['sponsor_id'],u['pnick'],u['comment'],"'%s'"%(u['timestamp'],)))

new_curs.execute("INSERT INTO channel_list (chan,userlevel,maxlevel) VALUES (%s,%s,%s)", ("#ascendancy",100,1000))

new_curs.execute("SELECT setval('user_list_id_seq',(select max(id) from user_list))")

new_conn.commit()
