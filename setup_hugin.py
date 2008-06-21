#!/usr/bin/python

# THIS FILE IS OLD, DEPRECATED AND USELESS, IGNORE IT

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
import ConfigParser

config = ConfigParser.ConfigParser
if not config.read("muninrc"):
    raise ValueError("Could not locate config file, "
                     "expected muninrc.")

DSN = "dbname=%s user=%s" % (config.get("Database", "dbname"),
                             config.get("Database", "user"))
conn=psycopg.connect(DSN)
cursor=conn.cursor()

updates = """
CREATE TABLE updates (
 id serial ,
 tick smallint UNIQUE,
 planets smallint,
 galaxies smallint,
 alliances smallint,
 PRIMARY KEY (id) 
)
"""

planet_canon = """
CREATE TABLE planet_canon (
 id serial,
 planetname varchar(20) NOT NULL,
 rulername varchar(20) NOT NULL,
 active boolean NOT NULL DEFAULT TRUE,
 PRIMARY KEY(id),
 UNIQUE (rulername,planetname)
)
"""

planet_dump = """
CREATE TABLE planet_dump (
 tick smallint REFERENCES updates (tick),
 x smallint,
 y smallint,
 z smallint,
 planetname varchar(20) NOT NULL,
 rulername varchar(20) NOT NULL,
 race char(3) NOT NULL CHECK (race in ('Ter','Cat','Xan','Zik')),
 size smallint NOT NULL,
 score integer NOT NULL,
 value integer NOT NULL,
 score_rank smallint NOT NULL,
 value_rank smallint NOT NULL,
 size_rank smallint NOT NULL,
 xp integer NOT NULL,
 xp_rank smallint NOT NULL,
 id integer NOT NULL REFERENCES planet_canon(id),
 PRIMARY KEY(tick, x, y, z),
 FOREIGN KEY(rulername,planetname) REFERENCES planet_canon (rulername,planetname)
)
"""

galaxy_canon = """
CREATE TABLE galaxy_canon (
 id serial,
 x smallint,
 y smallint,
 active boolean NOT NULL DEFAULT TRUE,
 PRIMARY KEY(id),
 UNIQUE(x,y)
)
"""

galaxy_dump = """
CREATE TABLE galaxy_dump (
 tick smallint REFERENCES updates (tick),
 x smallint,
 y smallint,
 name varchar(64) NOT NULL,
 size int NOT NULL,
 score bigint NOT NULL,
 value bigint NOT NULL,
 score_rank smallint NOT NULL,
 value_rank smallint NOT NULL,
 size_rank smallint NOT NULL,
 xp integer NOT NULL,
 xp_rank smallint NOT NULL,
 id integer NOT NULL REFERENCES galaxy_canon(id),
 PRIMARY KEY(tick, x, y),
 FOREIGN KEY(x,y) REFERENCES galaxy_canon (x,y)
)
"""

alliance_canon = """
CREATE TABLE alliance_canon (
 id serial,
 name varchar(16) UNIQUE,
 active boolean NOT NULL DEFAULT TRUE,
 PRIMARY KEY(id)
)
"""

alliance_dump = """
CREATE TABLE alliance_dump (
 tick smallint REFERENCES updates (tick),
 name varchar(16) NOT NULL REFERENCES alliance_canon (name),
 size int NOT NULL,
 members smallint NOT NULL,
 score bigint NOT NULL,
 score_rank smallint NOT NULL,
 size_rank smallint NOT NULL,
 members_rank smallint NOT NULL,
 score_avg int NOT NULL,
 size_avg smallint NOT NULL,
 id integer NOT NULL REFERENCES alliance_canon(id),
 PRIMARY KEY(tick, name)
)
"""

cursor.execute(updates)
print cursor.statusmessage
if cursor.statusmessage != 'CREATE TABLE':
    conn.rollback()
    raise

cursor.execute(planet_canon)
print cursor.statusmessage
if cursor.statusmessage != 'CREATE TABLE':
    conn.rollback()
    raise

cursor.execute(planet_dump)
print cursor.statusmessage
if cursor.statusmessage != 'CREATE TABLE':
    conn.rollback()
    raise

cursor.execute(galaxy_canon)
print cursor.statusmessage
if cursor.statusmessage != 'CREATE TABLE':
    conn.rollback()
    raise

cursor.execute(galaxy_dump)
print cursor.statusmessage
if cursor.statusmessage != 'CREATE TABLE':
    conn.rollback()
    raise

cursor.execute(alliance_canon)
print cursor.statusmessage
if cursor.statusmessage != 'CREATE TABLE':
    conn.rollback()
    raise

cursor.execute(alliance_dump)
print cursor.statusmessage
if cursor.statusmessage != 'CREATE TABLE':
    conn.rollback()
    raise    

conn.commit()
