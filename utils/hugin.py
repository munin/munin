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

import time

import ConfigParser
import os
import errno
from psycopg2 import psycopg1 as psycopg
import re
import traceback
import urllib2
import StringIO
import sys
import argparse

config = ConfigParser.ConfigParser()
if not config.read("muninrc"):
    # No config found.
    raise ValueError("Expected configuration file muninrc"
                     ", not found.")

useragent = "Munin (Python-urllib/%s); BotNick/%s; Admin/%s" % (urllib2.__version__,
                                                                config.get("Connection", "nick"),
                                                                config.get("Auth", "owner_nick"))

DSN = "dbname=%s user=%s" % (config.get("Database", "dbname"),
                             config.get("Database", "user"))
if config.has_option('Database', 'password'):
    DSN += ' password=%s' % config.get('Database', 'password')
if config.has_option('Database', 'host'):
    DSN += ' host=%s' % config.get('Database', 'host')

t_start = time.time()
t1 = t_start

ofile = file("pid.hugin", "w")
ofile.write("%s" % (os.getpid(),))
ofile.close()


def write_to_file(data, out):
    with open(out, 'w') as f:
        size = 16 * 1024
        chunk = True
        while chunk:
            chunk = data.read(size)
            if chunk:
                f.write(chunk)


def overwrite(from_file, to_file):
    try:
        os.unlink(to_file)
    except OSError:
        pass
    os.rename(from_file, to_file)


while True:
    try:
        round = config.getint('Planetarion', 'current_round')
        planetlist = config.get("Url", "planetlist")
        galaxylist = config.get("Url", "galaxylist")
        alliancelist = config.get("Url", "alliancelist")
        userfeedlist = config.get("Url", "userfeed")
        planet_file = planetlist.split('/')[-1]
        galaxy_file = galaxylist.split('/')[-1]
        alliance_file = alliancelist.split('/')[-1]
        userfeed_file = userfeedlist.split('/')[-1]
        write_dumps = config.getboolean('Dumps', 'write')
        from_web = False

        parser = argparse.ArgumentParser(
            description='Planetarion dumps processor for Munin.',
            epilog='Note that --planets, --galaxies, --alliances and --userfeed must either be given together, or not at all (in which case the most recent dumps are retrieved from the web)')
        parser.add_argument('-p', '--planets', type=argparse.FileType('r'), metavar='FILE')
        parser.add_argument('-g', '--galaxies', type=argparse.FileType('r'), metavar='FILE')
        parser.add_argument('-a', '--alliances', type=argparse.FileType('r'), metavar='FILE')
        parser.add_argument('-u', '--userfeed', type=argparse.FileType('r'), metavar='FILE')
        args = parser.parse_args()

        if args.planets and args.galaxies and args.alliances and args.userfeed:
            # ArgumentParser opens the files for us.
            planets = args.planets
            galaxies = args.galaxies
            alliances = args.alliances
            userfeed = args.userfeed
        elif args.planets or args.galaxies or args.alliances or args.userfeed:
            print "%s: error: The options --planets, --galaxies, --alliance and --userfeed must either be given together or not at all!\n" % (sys.argv[0])
            exit(3)
        else:
            # Read dumps from the web
            from_web = True
            try:
                req = urllib2.Request(planetlist)
                req.add_header('User-Agent', useragent)
                planets = urllib2.urlopen(req)
                if write_dumps:
                    write_to_file(planets, planet_file)
                    planets = open(planet_file, 'r')
            except Exception as e:
                print "Failed gathering planet listing."
                print e.__str__()
                time.sleep(300)
                continue
            try:
                req = urllib2.Request(galaxylist)
                req.add_header('User-Agent', useragent)
                galaxies = urllib2.urlopen(req)
                if write_dumps:
                    write_to_file(galaxies, galaxy_file)
                    galaxies = open(galaxy_file, 'r')
            except Exception as e:
                print "Failed gathering galaxy listing."
                print e.__str__()
                time.sleep(300)
                continue
            try:
                req = urllib2.Request(alliancelist)
                req.add_header('User-Agent', useragent)
                alliances = urllib2.urlopen(req)
                if write_dumps:
                    write_to_file(alliances, alliance_file)
                    alliances = open(alliance_file, 'r')
            except Exception as e:
                print "Failed gathering alliance listing."
                print e.__str__()
                time.sleep(300)
                continue
            try:
                req = urllib2.Request(userfeedlist)
                req.add_header('User-Agent', useragent)
                userfeed = urllib2.urlopen(req)
                if write_dumps:
                    write_to_file(userfeed, userfeed_file)
                    userfeed = open(userfeed_file, 'r')
            except Exception as e:
                print "Failed gathering user feed."
                print e.__str__()
                time.sleep(300)
                continue

        planets.readline()
        planets.readline()
        planets.readline()
        tick = planets.readline()
        m = re.search(r"tick:\s+(\d+)", tick, re.I)
        if not m:
            print "Invalid tick: '%s'" % (tick,)
            time.sleep(120)
            continue
        planet_tick = int(m.group(1))
        print "Planet dump for tick %s" % (planet_tick,)
        planets.readline()
        planets.readline()
        planets.readline()
        planets.readline()

        galaxies.readline()
        galaxies.readline()
        galaxies.readline()
        tick = galaxies.readline()
        m = re.search(r"tick:\s+(\d+)", tick, re.I)
        if not m:
            print "Invalid tick: '%s'" % (tick,)
            time.sleep(120)
            continue
        galaxy_tick = int(m.group(1))
        print "Galaxy dump for tick %s" % (galaxy_tick,)
        galaxies.readline()
        galaxies.readline()
        galaxies.readline()
        galaxies.readline()

        alliances.readline()
        alliances.readline()
        alliances.readline()
        alliances.readline()
        ptick = alliances.readline()
        m = re.search(r"tick:\s+(\d+)", tick, re.I)
        if not m:
            print "Invalid tick: '%s'" % (tick,)
            time.sleep(120)
            continue
        alliance_tick = int(m.group(1))
        print "Alliance dump for tick %s" % (alliance_tick,)
        alliances.readline()
        alliances.readline()
        alliances.readline()

        userfeed.readline()
        userfeed.readline()
        userfeed.readline()
        userfeed.readline()
        ptick = userfeed.readline()
        m = re.search(r"tick:\s+(\d+)", tick, re.I)
        if not m:
            print "Invalid tick: '%s'" % (tick,)
            time.sleep(120)
            continue
        userfeed_tick = int(m.group(1))
        print "User feed dump for tick %s" % (userfeed_tick,)
        userfeed.readline()
        userfeed.readline()
        userfeed.readline()

        if not (planet_tick == galaxy_tick == alliance_tick == userfeed_tick):
            print "Varying ticks found, sleeping"
            print "Planet: %s, Galaxy: %s, Alliance: %s, User feed: %s" % (planet_tick,
                                                                           galaxy_tick,
                                                                           alliance_tick,
                                                                           userfeed_tick)
            time.sleep(30)
            continue

        if from_web and write_dumps:
            # Store the newly retrieved dump files, removing the old ones
            # first, if they exist.
            dump_dir = config.get('Dumps', 'dir')
            tick_dir = os.path.join(dump_dir, "r%03d" % round, "%04d" % planet_tick)
            try:
                os.makedirs(tick_dir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            overwrite(planet_file, os.path.join(tick_dir, planet_file))
            overwrite(galaxy_file, os.path.join(tick_dir, galaxy_file))
            overwrite(alliance_file, os.path.join(tick_dir, alliance_file))
            overwrite(userfeed_file, os.path.join(tick_dir, userfeed_file))
            print 'Wrote dump files to disk'

        conn = psycopg.connect(DSN)
        cursor = conn.cursor()

        cursor.execute("SELECT max_tick(%s::smallint)", (round,))
        last_tick = cursor.fetchone()[0]
        if last_tick:
            last_tick = int(last_tick)
        if not last_tick:
            last_tick = -1

        if not planet_tick > last_tick:
            if from_web:
                print "Stale ticks found, sleeping"
                time.sleep(60)
                continue
            else:
                print "Warning: stale ticks found, but dump files were passed on command line, continuing"

        t2 = time.time() - t1
        if from_web:
            print "Loaded dumps from webserver in %.3f seconds" % (t2,)
        else:
            print "Loaded dumps from file in %.3f seconds" % (t2,)
        t1 = time.time()

        ptmp = 'ptmp'
        gtmp = 'gtmp'
        atmp = 'atmp'
        utmp = 'utmp'

        query = """
        CREATE TEMP TABLE %s (
         uid varchar(12) NOT NULL,
         x smallint,
         y smallint,
         z smallint,
         planetname varchar(22) NOT NULL,
         rulername varchar(32) NOT NULL,
         race char(3) CHECK (race in (NULL,'Ter','Cat','Xan','Zik','Etd')),
         size integer NOT NULL,
         score integer NOT NULL,
         value integer NOT NULL,
         xp integer NOT NULL,
         special varchar(10) NOT NULL
         )
        """ % (ptmp,)
        cursor.execute(query)
        foo = planets.readlines()[:-1]
        foo = map(lambda f: f.decode('iso-8859-1').encode('utf8'), foo)

        cursor.copy_from(StringIO.StringIO(''.join(foo)), ptmp, "\t")

        query = """
        CREATE TEMP TABLE %s (
         x smallint,
         y smallint,
         name varchar(66) NOT NULL,
         size int NOT NULL,
         score bigint DEFAULT 0,
         value bigint NOT NULL,
         xp integer NOT NULL
        )
        """ % (gtmp,)
        cursor.execute(query)
        foo = galaxies.readlines()[:-1]
        foo = map(lambda f: f.decode('iso-8859-1').encode('utf8'), foo)

        cursor.copy_from(StringIO.StringIO(''.join(foo)), gtmp, "\t", null="")

        query = """
        CREATE TEMP TABLE %s (
         score_rank smallint NOT NULL,
         name varchar(22) NOT NULL,
         size int NOT NULL,
         members smallint NOT NULL,
         score bigint NOT NULL,
         points bigint NOT NULL,
         total_score bigint NOT NULL,
         total_value bigint NOT NULL
        )
        """ % (atmp,)
        cursor.execute(query)
        foo = alliances.readlines()[:-1]
        foo = map(lambda f: f.decode('iso-8859-1').encode('utf8'), foo)

        cursor.copy_from(StringIO.StringIO(''.join(foo)), atmp, "\t")

        query = """
        CREATE TEMP TABLE %s (
         tick smallint NOT NULL,
         type varchar(32) NOT NULL,
         text varchar(255) NOT NULL
        )
        """ % (utmp,)
        cursor.execute(query)
        foo = userfeed.readlines()[:-1]
        foo = map(lambda f: f.decode('iso-8859-1').encode('utf8'), foo)

        cursor.copy_from(StringIO.StringIO(''.join(foo)), utmp, "\t")

        t2 = time.time() - t1
        print "Copied dumps in %.3f seconds" % (t2,)
        t1 = time.time()

        query = "SELECT store_update(%s::smallint,%s::smallint,%s::text,%s::text,%s::text,%s::text)"
        cursor.execute(query, (round, planet_tick, ptmp, gtmp, atmp, utmp))

        try:

            query = "SELECT store_planets(%s::smallint,%s::smallint)"
            cursor.execute(query, (round, planet_tick,))
            t2 = time.time() - t1
            print "Processed and inserted planet dumps in %.3f seconds" % (t2,)
            t1 = time.time()

            query = "SELECT store_galaxies(%s::smallint,%s::smallint)"
            cursor.execute(query, (round, galaxy_tick,))
            t2 = time.time() - t1
            print "Processed and inserted galaxy dumps in %.3f seconds" % (t2,)
            t1 = time.time()

            query = "SELECT store_alliances(%s::smallint,%s::smallint)"
            cursor.execute(query, (round, alliance_tick,))
            t2 = time.time() - t1
            print "Processed and inserted alliance dumps in %.3f seconds" % (t2,)
            t1 = time.time()

            query = "SELECT store_userfeed(%s::smallint)"
            cursor.execute(query, (round,))
            t2 = time.time() - t1
            print "Processed and inserted user feed dumps in %.3f seconds" % (t2,)
            t1 = time.time()

            planets.close()
            galaxies.close()
            alliances.close()
            userfeed.close()

        except psycopg.IntegrityError:
            raise
        # raise Exception("IntegrityError on dump inserts. Tick number has already
        # been validated above, so that means something else is not unique on PA's
        # end that should be and PA team fucked up again. Go and whine in
        # #support.")

        conn.commit()
        break
    except Exception as e:
        print "Something random went wrong, sleeping for 15 seconds to hope it improves"
        print e.__str__()
        traceback.print_exc()
        time.sleep(15)
        continue


t2 = time.time() - t1
t1 = time.time() - t_start
print "Commit in %.3f seconds" % (t2,)
print "Total time taken: %.3f seconds" % (t1,)

while True:
    try:
        conn = psycopg.connect(DSN)
        cursor = conn.cursor()

        cursor.execute("SELECT MIN(tick) FROM updates WHERE tick > 0")
        min_tick = int(cursor.fetchone()[0])
        if not min_tick:
            min_tick = -1

        query = "DELETE FROM epenis_cache"
        cursor.execute(query)
        query = "CREATE TEMP SEQUENCE activity_rank"
        cursor.execute(query)

        query = "INSERT INTO epenis_cache (planet_id, epenis, epenis_rank) "
        query += " SELECT *,nextval('activity_rank') AS activity_rank"
        query += " FROM (SELECT t1.id, t1.score-t5.score AS activity"
        query += " FROM planet_dump AS t1"
        query += " INNER JOIN planet_dump AS t5"
        query += " ON t1.id=t5.id"
        query += " WHERE t1.tick = (select max(tick) from updates)"
        query += " AND t5.tick = GREATEST(t1.tick - 72, %s)"
        query += " ORDER BY activity DESC) AS t8;"
        cursor.execute(query, (min_tick,))

        conn.commit()
        break
    except Exception as e:
        print "Something random went wrong, sleeping for 15 seconds to hope it improves"
        print e.__str__()
        traceback.print_exc()
        time.sleep(15)
        continue

print "Generated epenis_cache"
