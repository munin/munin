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
import psycopg


class migrator:
    def __init__(self,cursor):
        self.cursor=cursor

    def add_padding(self):
        for i in xrange(1,92):
            prop=self.find_single_prop_by_id(i)
            if not prop or prop['active'] or prop['padding']:
                continue

            (voters, yes, no) = self.get_voters_for_prop(prop['id'])
            (winners,losers,winning_total,losing_total)=self.get_winners_and_losers(voters,yes,no)
            query="UPDATE %s_proposal SET "%(prop['prop_type'],)
            query+=" vote_result=%s,compensation=%d"
            query+=" WHERE id=%d"
            args=(['no','yes'][yes>no],losing_total,prop['id'])
            print query%args
            self.cursor.execute(query,args)
            if self.cursor.rowcount < 1:
                print "argh!"


    def find_single_prop_by_id(self,prop_id):
        query="SELECT id, prop_type, proposer, person, created, padding, comment_text, active, closed FROM ("
        query+="SELECT t1.id AS id, 'invite' AS prop_type, t2.pnick AS proposer, t1.person AS person, t1.padding AS padding, t1.created AS created,"
        query+=" t1.comment_text AS comment_text, t1.active AS active, t1.closed AS closed"
        query+=" FROM invite_proposal AS t1 INNER JOIN user_list AS t2 ON t1.proposer_id=t2.id UNION ("
        query+=" SELECT t3.id AS id, 'kick' AS prop_type, t4.pnick AS proposer, t5.pnick AS person, t3.padding AS padding, t3.created AS created,"
        query+=" t3.comment_text AS comment_text, t3.active AS active, t3.closed AS closed"
        query+=" FROM kick_proposal AS t3"
        query+=" INNER JOIN user_list AS t4 ON t3.proposer_id=t4.id"
        query+=" INNER JOIN user_list AS t5 ON t3.person_id=t5.id)) AS t6 WHERE t6.id=%d"

        self.cursor.execute(query,(prop_id,))
        return self.cursor.dictfetchone()

    def get_winners_and_losers(self,voters,yes,no):
        if yes > no:
            losers=voters['no']
            winners=voters['yes']
            winning_total=yes
            losing_total=no
        else:
            winners=voters['no']
            losers=voters['yes']
            winning_total=no
            losing_total=yes
        return (winners,losers,winning_total,losing_total)


    def get_voters_for_prop(self,prop_id):
        query="SELECT t1.vote AS vote,t1.carebears AS carebears"
        query+=", t1.prop_id AS prop_idd,t1.voter_id AS voter_id,t2.pnick AS pnick"
        query+=" FROM prop_vote AS t1"
        query+=" INNER JOIN user_list AS t2 ON t1.voter_id=t2.id"
        query+=" WHERE prop_id=%d"
        self.cursor.execute(query,(prop_id,))
        voters={}
        voters['yes']=[]
        voters['no']=[]
        voters['abstain']=[]
        yes=0;no=0

        for r in self.cursor.dictfetchall():
            if r['vote'] == 'yes':
                yes+=r['carebears']
                voters['yes'].append(r)
            elif r['vote'] == 'no':
                no+=r['carebears']
                voters['no'].append(r)
            elif r['vote'] == 'abstain':
                voters['abstain'].append(r)
        return (voters, yes, no)



user="munin"
db="patools30"
conn=psycopg.connect("user=%s dbname=%s" %(user,db))
conn.serialize()
conn.autocommit()
curs=conn.cursor()
m=migrator(curs)
m.add_padding()

