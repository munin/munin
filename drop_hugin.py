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

import psycopg

conn=psycopg.connect("dbname=patools16 user=andreaja")
cursor=conn.cursor()

cursor.execute("DROP TABLE planet_dump")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE planet_canon")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE galaxy_dump")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE galaxy_canon")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE alliance_dump")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE alliance_canon")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE updates")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

conn.commit()
