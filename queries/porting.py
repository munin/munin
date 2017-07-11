#!/usr/bin/env python

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

from psycopg2 import psycopg1 as psycopg
import sys, pprint

pp = pprint.PrettyPrinter(indent=4)

user="munin"

try:
    old_db=sys.argv[1]
    new_db=sys.argv[2]
    # if new_db == 'patools':
    #     raise
except:
    print "Usage: %s <old_db> <new_db>" % (sys.argv[0])
    sys.exit(0)

old_conn=psycopg.connect("user=%s dbname=%s" %(user,old_db))
new_conn=psycopg.connect("user=%s dbname=%s" %(user,new_db))

old_curs=old_conn.cursor()
new_curs=new_conn.cursor()

old_round = int(old_db.split('patools')[1])

# updates

def port(table_name, results, map_columns=[], mappings=[],round_nr=old_round):
    num = 0
    mapout = {}
    for u in results:
        if table_name == 'development' and not u.has_key('population'):
            u['population']=5

        column_names = [c for c in u.keys() if c != 'id' and c not in map_columns]
        values = map(lambda n: u[n],column_names)

        if round_nr > 0:
            column_names.append('round')
            values.append(round_nr)

        for i in range(0,len(map_columns)):
            if not u[map_columns[i]]:
                continue
            column_names.append(map_columns[i])
            values.append(mappings[i][u[map_columns[i]]])


        columns = ', '.join(column_names)
        values_format = ', '.join(['%s']*len(values))

        q = "INSERT INTO %s (%s) VALUES (%s)" % (table_name, columns, values_format)
        if u.has_key('id'):
            q+="  RETURNING (id)"

        new_curs.execute(q, values)

        if u.has_key('id'):
            new_id = new_curs.dictfetchone()['id']
            mapout[u['id']]=new_id
        num += 1
        if num % 100000 == 0:
            print "%d" % (num,)
    return mapout


def port_user_list(table_name, results, map_columns, mappings):
    for u in results:
        u['user_id']=u['id']
        port(table_name, [u], map_columns, mappings)


def port_planet_canon(table_name, results, map_columns=[], mappings=[], round_nr=old_round):
    mapout={}
    if round_nr > 67:
        return port(table_name, results, map_columns, mappings, round_nr)
    else:
        for u in results:
            u['uid']="%s-%s" % (u.pop('planetname'), u.pop('rulername'))
            mapout.update(port(table_name, [u], map_columns, mappings, round_nr))
        return mapout

old_curs.execute("SELECT * FROM updates where tick > -1")
port('updates', old_curs.dictfetchall())
print "Updates from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM planet_canon")
planet_mapping = port_planet_canon('planet_canon', old_curs.dictfetchall())
print "planet_canon from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM planet_dump")
port('planet_dump', old_curs.dictfetchall(), ['id'], [planet_mapping])
print "planet_dump from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM galaxy_canon")
galaxy_mapping = port('galaxy_canon', old_curs.dictfetchall())
print "galaxy_canon from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM galaxy_dump")
port('galaxy_dump', old_curs.dictfetchall(), ['id'], [galaxy_mapping])
print "galaxy_dump from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM alliance_canon")
alliance_mapping = port('alliance_canon', old_curs.dictfetchall())
print "alliance_canon from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM alliance_dump")
port('alliance_dump', old_curs.dictfetchall(), ['id'], [alliance_mapping])
print "alliance_dump from round %s inserted" % (old_round,)

if old_round > 67:
    old_curs.execute("SELECT * FROM userfeed_dump")
    port('userfeed_dump', old_curs.dictfetchall())
    print "userfeed_dump from round %s inserted" % (old_round,)

if old_round > 67:
    old_curs.execute("SELECT * FROM anarchy")
    port('anarchy', old_curs.dictfetchall(), ['pid'], [planet_mapping])
    print "anarchy from round %s inserted" % (old_round,)

if old_round > 67:
    old_curs.execute("SELECT * FROM alliance_relation")
    port('alliance_relation', old_curs.dictfetchall(), ['acceptor', 'initiator'], [alliance_mapping, alliance_mapping])
    print "alliance_relation from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM command_log")
port('command_log', old_curs.dictfetchall(), round_nr=-1)
print "command_log from round %s inserted" % (old_round,)

old_curs.execute("SELECT id, planet_id FROM user_list")
port_user_list('round_user_pref', old_curs.dictfetchall(), ['planet_id'], [planet_mapping])
print "user_list from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM ship")
ship_mapping = port('ship', old_curs.dictfetchall())
print "ship from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM intel")
port('intel', old_curs.dictfetchall(), ['pid', 'alliance_id'],[planet_mapping,alliance_mapping])
print "intel from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM scan")
scan_mapping = port('scan', old_curs.dictfetchall(), ['pid'], [planet_mapping])
print "scan from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM planet")
port('planet', old_curs.dictfetchall(), ['scan_id'], [scan_mapping], round_nr=-1)
print "planet from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM development")
port('development', old_curs.dictfetchall(), ['scan_id'], [scan_mapping], round_nr=-1)
print "development from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM unit")
port('unit', old_curs.dictfetchall(), ['scan_id', 'ship_id'], [scan_mapping, ship_mapping], round_nr=-1)
print "unit from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM au")
port('au', old_curs.dictfetchall(), ['scan_id', 'ship_id'], [scan_mapping, ship_mapping], round_nr=-1)
print "au from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM fleet")
fleet_mapping = port('fleet', old_curs.dictfetchall(), ['scan_id', 'owner_id', 'target'], [scan_mapping, planet_mapping, planet_mapping])
print "fleet from round %s inserted" % (old_round,)

old_curs.execute("SELECT * FROM fleet_content")
fleet_content_mapping = port('fleet_content', old_curs.dictfetchall(), ['fleet_id', 'ship_id'], [fleet_mapping, ship_mapping])
print "fleet_content from round %s inserted" % (old_round,)


#new_conn.commit()
