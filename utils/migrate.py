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

user = "munin"

try:
    old_db = sys.argv[1]
    new_db = sys.argv[2]
except BaseException:
    print "Usage: %s <old_db> <new_db>" % (sys.argv[0])
    sys.exit(0)


old_conn = psycopg.connect("user=%s dbname=%s" % (user, old_db))
new_conn = psycopg.connect("user=%s dbname=%s" % (user, new_db))

old_curs = old_conn.cursor()

new_curs = new_conn.cursor()

old_curs.execute(
    "SELECT id, pnick,userlevel,alias_nick,sponsor, phone, pubphone, passwd, salt, carebears, available_cookies, last_cookie_date  FROM user_list")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO user_list (id,pnick,userlevel,alias_nick,sponsor,phone,pubphone,passwd,salt,carebears,available_cookies,last_cookie_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (
        u['id'], u['pnick'], u['userlevel'], u['alias_nick'], u['sponsor'], u['phone'], [False, True][int(u['pubphone'])], u['passwd'], u['salt'], u['carebears'], u['available_cookies'], u['last_cookie_date']))

old_curs.execute("SELECT user_id, friend_id FROM phone")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO phone (user_id,friend_id) VALUES (%s,%s)", (u['user_id'], u['friend_id']))

old_curs.execute("SELECT t1.quote AS quote FROM quote AS t1")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO quote (quote) VALUES (%s)", (u['quote'],))

old_curs.execute("SELECT t1.slogan AS slogan FROM slogan AS t1")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO slogan (slogan) VALUES (%s)", (u['slogan'],))

new_curs.execute("INSERT INTO channel_list (chan,userlevel,maxlevel) VALUES (%s,%s,%s)", ("#ascendancy", 100, 1000))
new_curs.execute("INSERT INTO channel_list (chan,userlevel,maxlevel) VALUES (%s,%s,%s)", ("#meanies", 1, 1000))

new_curs.execute("SELECT setval('user_list_id_seq',(select max(id) from user_list))")

old_curs.execute(
    "SELECT id,active,proposer_id,person,created,closed,comment_text,vote_result,compensation,padding FROM invite_proposal")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO invite_proposal (id,active,proposer_id,person,created,closed,comment_text,vote_result,compensation,padding) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                     (u['id'], [False, True][int(u['active'])], u['proposer_id'], u['person'], u['created'], u['closed'], u['comment_text'], u['vote_result'], u['compensation'], u['padding']))

old_curs.execute(
    "SELECT id,active,proposer_id,person_id,created,closed,comment_text,vote_result,compensation,padding FROM kick_proposal")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO kick_proposal (id,active,proposer_id,person_id,created,closed,comment_text,vote_result,compensation,padding) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (u['id'], [
                     False, True][int(u['active'])], u['proposer_id'], u['person_id'], u['created'], u['closed'], u['comment_text'], u['vote_result'], u['compensation'], u['padding']))

new_curs.execute(
    "SELECT setval('proposal_id_seq',(select max(id) from (select id from invite_proposal union select id from kick_proposal) t1))")

old_curs.execute("SELECT vote,carebears,prop_id,voter_id FROM prop_vote")

for u in old_curs.dictfetchall():
    new_curs.execute("INSERT INTO prop_vote (vote,carebears,prop_id,voter_id) VALUES (%s,%s,%s,%s)",
                     (u['vote'], u['carebears'], u['prop_id'], u['voter_id']))

old_curs.execute("SELECT log_time, year_number, week_number, howmany, giver, receiver FROM cookie_log")

for u in old_curs.dictfetchall():
    new_curs.execute(
        "INSERT INTO cookie_log (log_time, year_number, week_number, howmany, giver, receiver) VALUES (%s,%s,%s,%s,%s,%s)",
        (u['log_time'],
         u['year_number'],
            u['week_number'],
            u['howmany'],
            u['giver'],
            u['receiver']))


new_conn.commit()
