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

import munin.loadable as loadable
import psycopg2
import re
import threading
import traceback
import urllib.request, urllib.error, urllib.parse
import dateutil.parser


class scan(threading.Thread):
    # rand_id is the Planetarion scan ID; group_id is the Planetarion scan
    # group ID, if any. client is for debug ONLY
    def __init__(self, rand_id, client, config, nick, pnick, group_id):
        self.rand_id = rand_id
        self.client = client
        self.config = config
        self.connection = self.create_conn()
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        self.nick = nick
        self.pnick = pnick
        self.group_id = group_id
        self.useragent = "Munin (Python-urllib/%s); BotNick/%s; Admin/%s" % (
            urllib.request.__version__,
            config.get("Connection", "nick"),
            config.get("Auth", "owner_nick"),
        )
        threading.Thread.__init__(self)

    def create_conn(self):
        dsn = "user=%s dbname=%s" % (
            self.config.get("Database", "user"),
            self.config.get("Database", "dbname"),
        )
        if self.config.has_option("Database", "password"):
            dsn += " password=%s" % self.config.get("Database", "password")
        if self.config.has_option("Database", "host"):
            dsn += " host=%s" % self.config.get("Database", "host")

        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        return conn

    def run(self):
        try:
            self.unsafe_method()
        except Exception as e:
            print("Exception in scan: " + e.__str__())
            traceback.print_exc()

    def unsafe_method(self):
        if self.group_id:
            req = urllib.request.Request(
                "http://game.planetarion.com/showscan.pl?scan_grp="
                + self.group_id
                + "&inc=1"
            )
            req.add_header("User-Agent", self.useragent)
            page = urllib.request.urlopen(req).read().decode("ISO-8859-1")
            for scan in page.split("<hr>"):
                m = re.search("scan_id=([0-9a-zA-Z]+)", scan)
                if m:
                    self.rand_id = m.group(1)
                    try:
                        self.execute(scan)
                    except Exception as e:
                        print("Exception in scan: " + e.__str__())
                        traceback.print_exc()
        else:
            self.unsafe_method2()

    def unsafe_method2(self):
        req = urllib.request.Request(
            "http://game.planetarion.com/showscan.pl?scan_id=" + self.rand_id + "&inc=1"
        )
        req.add_header("User-Agent", self.useragent)
        page = urllib.request.urlopen(req).read().decode("ISO-8859-1")
        self.execute(page)

    def execute(self, page):
        m = re.search(">([^>]+) on (\d+)\:(\d+)\:(\d+) in tick (\d+)", page)
        if not m:
            print("Expired/non-matching scan (id: %s)" % (self.rand_id,))
            return

        round = self.config.getint("Planetarion", "current_round")

        scantype = self.name_to_type(m.group(1))
        x = m.group(2)
        y = m.group(3)
        z = m.group(4)
        tick = m.group(5)
        m = re.search("Scan time: ([^<]+)", page)
        scan_time = None
        if m:
            scan_time = dateutil.parser.parse(m.group(1))

        p = loadable.planet(x, y, z)
        # This fails if this planet exiled in this tick.
        if not p.load_most_recent(self.cursor, round):
            return

        self.cursor.execute("BEGIN;")
        query = "INSERT INTO scan"
        query += " (round, tick, pid, nick, pnick, scantype, rand_id, group_id, scan_time)"
        query += " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        query += " RETURNING id"
        next_id = -1
        try:
            self.cursor.execute(
                query,
                (
                    round,
                    tick,
                    p.id,
                    self.nick,
                    self.pnick,
                    scantype,
                    self.rand_id,
                    self.group_id,
                    scan_time,
                ),
            )
            next_id = self.cursor.fetchone()["id"]
        except psycopg2.errors.UniqueViolation as uv:
            print("Scan with ID %s already exists, nothing to do" % (
                self.rand_id,
            ))
            self.cursor.execute("ROLLBACK")
        except psycopg2.Error as e:
            print("Failed to insert scan with ID %s:\n%s" % (
                self.rand_id,
                e.__str__(),
            ))
            self.cursor.execute("ROLLBACK")
        else:
            try:
                if scantype == "planet":
                    self.parse_planet(next_id, page)
                elif scantype == "development":
                    self.parse_development(next_id, page)
                elif scantype == "unit":
                    self.parse_unit(next_id, page, "unit", round)
                elif scantype == "news":
                    self.parse_news(next_id, page, round)
                elif scantype == "incoming":
                    self.parse_incoming(next_id, page, round)
                elif scantype == "jgp":
                    self.parse_jumpgate(next_id, page, round)
                elif scantype == "au":
                    self.parse_unit(next_id, page, "au", round)
                elif scantype == "military":
                    self.parse_military(next_id, page, "military", round)
                else:
                    raise Exception("Unknown scan type")
            except Exception as e:
                print("Failed to insert scan of type %s and ID %s: %s" % (
                    scantype,
                    self.rand_id,
                    e.__str__(),
                ))
                traceback.print_exc()
                self.cursor.execute("ROLLBACK;")
            else:
                # All went well.
                self.cursor.execute("COMMIT;")

    def name_to_type(self, name):
        if name == "Jumpgate Probe":
            return "jgp"
        elif name == "Advanced Unit Scan":
            return "au"
        else:
            return name.split(" ")[0].lower();

    def parse_news(self, scan_id, page, round):
        m = re.search("on (\d+)\:(\d+)\:(\d+) in tick (\d+)", page)
        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        tick = m.group(4)

        p = loadable.planet(x, y, z)
        # This fails if this planet exiled in this tick.
        if not p.load_most_recent(self.cursor, round):
            print("Failed to load planet from coords %s:%s:%s for news scan" % (
                x,
                y,
                z,
            ))
            return

        # incoming fleets
        # <tr class="shadedbackground2"><td class="left vtop">Incoming</td><td class="vtop">277</td><td class="left vtop">We have detected an open jumpgate from Wonder Woman, located at <a class="coords" href="galaxy.pl?x=8&amp;y=3">8:3:3</a>. The fleet will approach our system in tick 285 and appears to have 0 visible ships.</td></tr>
        for m in re.finditer(
                '<tr[^>]*><td[^>]*>Incoming</td><td[^>]*>(\d+)</td><td[^>]*>We have detected an open jumpgate from ([^<]+), located at <a[^>]*>(\d+):(\d+):(\d+)</a>. The fleet will approach our system in tick (\d+) and appears to have (\d+) visible ships.</td></tr>',
                page,
        ):
            newstick = m.group(1)
            fleetname = m.group(2)
            originx = m.group(3)
            originy = m.group(4)
            originz = m.group(5)
            arrivaltick = m.group(6)
            numships = m.group(7)

            owner = loadable.planet(originx, originy, originz)
            if owner.load_most_recent(self.cursor, round):
                query  = "INSERT INTO fleet (round, scan_id, owner_id, target, fleet_size, fleet_name, launch_tick, landing_tick, mission)"
                query += " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'unknown')"
                query += " ON CONFLICT      (round,          owner_id, target,             fleet_name,              landing_tick)"
                # The mission is not specified for incoming fleets on news
                # scans, so don't update whatever might already be there.
                query += " DO UPDATE SET scan_id=EXCLUDED.scan_id, fleet_size=EXCLUDED.fleet_size"
                # TODO: Perhaps we should not 'upgrade' fleets from JGPs to
                # fleets from news scans at all? Is older but complete info
                # from a JGP better than newer but incomplete info from a news
                # scan? If so: query += " WHERE mission = 'unknown'" (and a
                # similar clause for outgoing fleets below).

                self.cursor.execute(
                    query,
                    (
                        round,
                        scan_id,
                        owner.id,
                        p.id,
                        numships,
                        fleetname,
                        newstick,
                        arrivaltick,
                    )
                )
                # print(
                #     "Incoming:"
                #     + newstick
                #     + ":"
                #     + fleetname
                #     + "-"
                #     + originx
                #     + ":"
                #     + originy
                #     + ":"
                #     + originz
                #     + "-"
                #     + arrivaltick
                #     + "-"
                #     + numships
                # )

        # launched defending fleets:
        # <tr class="shadedbackground"><td class="left vtop">Launch</td><td class="vtop">277</td><td class="left vtop">The help is on the way fleet has been launched, heading for <a class="coords" href="galaxy.pl?x=4&amp;y=4">4:4:5</a>, on a mission to Defend. Arrival tick: 283</td></tr>
        # launched attacking fleets:
        # <tr class="shadedbackground"><td class="left vtop">Launch</td><td class="vtop">277</td><td class="left vtop">The time to go fleet has been launched, heading for <a class="coords" href="galaxy.pl?x=1&amp;y=2">1:2:2</a>, on a mission to Attack. Arrival tick: 284</td></tr>

        for m in re.finditer(
                '<tr[^>]*><td[^>]*>Launch</td><td[^>]*>(\d+)</td><td[^>]*>The ([^,]+) fleet has been launched, heading for <a[^>]*>(\d+):(\d+):(\d+)</a>, on a mission to (Defend|Attack). Arrival tick: (\d+)</td></tr>',
                page,
        ):
            newstick = m.group(1)
            fleetname = m.group(2)
            originx = m.group(3)
            originy = m.group(4)
            originz = m.group(5)
            mission = m.group(6).lower()
            arrivaltick = m.group(7)

            target = loadable.planet(originx, originy, originz)
            if target.load_most_recent(self.cursor, round):
                query  = "INSERT INTO fleet (round, scan_id, owner_id, target, fleet_name, launch_tick, landing_tick, mission)"
                query += " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                query += " ON CONFLICT      (round,          owner_id, target, fleet_name,              landing_tick)"
                # The fleet size is not specified for outgoing fleets on news
                # scans, so don't update whatever might already be there.
                query += " DO UPDATE SET scan_id=EXCLUDED.scan_id, mission=EXCLUDED.mission, launch_tick=EXCLUDED.launch_tick"
                self.cursor.execute(
                    query,
                    (
                        round,
                        scan_id,
                        p.id,
                        target.id,
                        fleetname,
                        newstick,
                        arrivaltick,
                        mission,
                    )
                )
                # print(
                #     "Launch:"
                #     + newstick
                #     + ":"
                #     + fleetname
                #     + ":"
                #     + originx
                #     + ":"
                #     + originy
                #     + ":"
                #     + originz
                #     + ":"
                #     + arrivaltick
                #     + ":"
                #     + mission
                # )

        # TODO: All this fleet parsing reads to me like the original intent was
        # to build a complete picture of fleet movement the universe, and
        # provide commands to track fleets beyond merely regurgitating JGP data
        # through the !jgp command. Right now, though, fleets that recall are
        # not included in that theoretical picture: once a fleet is launched,
        # it remains launched until its original landing tick.
        #
        # Recalls could be parsed from both news scans (news scans explicitly
        # include 'Recall' entries) and JGPs (outgoing fleets that disappear
        # from JGPs and returning fleets that appear on JGPs before their
        # landing tick must've been recalled).
        #
        # Possible uses for this information:
        # - Detect fake defense by showing other fleets launched by the planet
        #   defending against you.
        # - Offer potential fleetcatch targets.
        # - Show whether your target has fleets out.

        # tech report
        # <td class=left valign=top>Tech</td><td valign=top>838</td><td class=left valign=top>Our scientists report that Portable EMP emitters has been finished. Please drop by the Research area and choose the next area of interest.</td>
        # <tr class="shadedbackground2"><td class="left vtop">Tech</td><td class="vtop">275</td><td class="left vtop">Our scientists report that Heavy Cargo Transfers IV has been finished. Please drop by the <a href="research.pl">Research area</a> and choose the next area of interest.</td></tr>
        for m in re.finditer(
                '<tr[^>]*><td[^>]*>Tech</td><td[^>]*>(\d+)</td><td[^>]*>Our scientists report that ([^<]+) has been finished\. Please drop by the <a href="research\.pl">Research area</a> and choose the next area of interest\.</td></tr>',
                page,
        ):
            newstick = m.group(1)
            research = m.group(2)

            # print("Tech:" + newstick + ":" + research)

        # failed security report
        # <tr class="shadedbackground"><td class="left vtop">Security</td><td class="vtop">270</td><td class="left vtop">A covert operation was attempted by mz (<a class="coords" href="galaxy.pl?x=2&amp;y=3">2:3:1</a>), but our security guards were able to stop them from doing any harm. Your guards have successfully killed the intruders.</td></tr>
        # <td class=left valign=top>Security</td><td valign=top>873</td><td class=left valign=top>A covert operation was attempted by Ikaris (2:5:5), but our agents were able to stop them from doing any harm.</td>
        for m in re.finditer(
                '<tr[^>]*><td[^>]*>Security</td><td[^>]*>(\d+)</td><td[^>]*>A covert operation was attempted by ([^<]+) \\(<a[^>]*">(\d+):(\d+):(\d+)</a>\\), but our security guards were able to stop them from doing any harm.[^<]*</td></tr>',
                page,
        ):
            newstick = m.group(1)
            ruler = m.group(2)
            originx = m.group(3)
            originy = m.group(4)
            originz = m.group(5)
            covopper = loadable.planet(originx, originy, originz)
            if covopper.load_most_recent(self.cursor, round):
                query  = "INSERT INTO covop (scan_id, covopper, target)"
                query += " VALUES (%s, %s, %s)"
                self.cursor.execute(
                    query,
                    (
                        scan_id,
                        covopper.id,
                        p.id,
                    )
                )
                # print(
                #     "Security:"
                #     + newstick
                #     + ":"
                #     + ruler
                #     + ":"
                #     + originx
                #     + ":"
                #     + originy
                #     + ":"
                #     + originz
                # )

        # fleet report
        # <tr bgcolor=#2d2d2d><td class=left valign=top>Fleet</td><td valign=top>881</td><td class=left valign=top><table width=500><tr><th class=left colspan=3>Report of Losses from the Disposable Heroes fighting at 13:10:3</th></tr>
        # <tr><th class=left width=33%>Ship</th><th class=left width=33%>Arrived</th><th class=left width=33%>Lost</th></tr>
        #
        # <tr><td class=left>Syren</td><td class=left>15</td><td class=left>13</td></tr>
        # <tr><td class=left>Behemoth</td><td class=left>13</td><td class=left>13</td></tr>
        # <tr><td class=left>Roach</td><td class=left>6</td><td class=left>6</td></tr>
        # <tr><td class=left>Thief</td><td class=left>1400</td><td class=left>1400</td></tr>
        # <tr><td class=left>Clipper</td><td class=left>300</td><td class=left>181</td></tr>
        #
        # <tr><td class=left>Buccaneer</td><td class=left>220</td><td class=left>102</td></tr>
        # <tr><td class=left>Rogue</td><td class=left>105</td><td class=left>105</td></tr>
        # <tr><td class=left>Marauder</td><td class=left>110</td><td class=left>110</td></tr>
        # <tr><td class=left>Ironclad</td><td class=left>225</td><td class=left>90</td></tr>
        # </table>
        #
        # <table width=500><tr><th class=left colspan=3>Report of Ships Stolen by the Disposable Heroes fighting at 13:10:3</th></tr>
        # <tr><th class=left width=50%>Ship</th><th class=left width=50%>Stolen</th></tr>
        # <tr><td class=left>Roach</td><td class=left>5</td></tr>
        # <tr><td class=left>Hornet</td><td class=left>1</td></tr>
        # <tr><td class=left>Wraith</td><td class=left>36</td></tr>
        # </table>
        # <table width=500><tr><th class=left>Asteroids Captured</th><th class=left>Metal : 37</th><th class=left>Crystal : 36</th><th class=left>Eonium : 34</th></tr></table>
        #
        # </td></tr>

        # print("Parsed news scan on %s:%s:%s" % (x, y, z,))

    def parse_planet(self, scan_id, page):
        m = re.search("on (\d+)\:(\d+)\:(\d+) in tick (\d+)", page)
        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        tick = m.group(4)

        # m = re.search('<tr><td class="left">Asteroids</td><td>(\d+)</td><td>(\d+)</td><td>(\d+)</td></tr><tr><td class="left">Resources</td><td>(\d+)</td><td>(\d+)</td><td>(\d+)</td></tr><tr><th>Score</th><td>(\d+)</td><th>Value</th><td>(\d+)</td></tr>', page)
        # m = re.search(r"""<tr><td class="left">Asteroids</td><td>(\d+)</td><td>(\d+)</td><td>(\d+)</td></tr><tr><td class="left">Resources</td><td>(\d+)</td><td>(\d+)</td><td>(\d+)</td></tr><tr><th>Score</th><td>(\d+)</td><th>Value</th><td>(\d+)</td></tr>""", page)

        page = re.sub(",", "", page)
        m = re.search(
            r"""
            <tr><td[^>]*>Metal</td><td[^>]*>(\d+)</td><td[^>]*>(\d+)</td></tr>\s*
            <tr><td[^>]*>Crystal</td><td[^>]*>(\d+)</td><td[^>]*>(\d+)</td></tr>\s*
            <tr><td[^>]*>Eonium</td><td[^>]*>(\d+)</td><td[^>]*>(\d+)</td></tr>\s*
        """,
            page,
            re.VERBOSE,
        )
        roid_m = m.group(1)
        res_m = m.group(2)
        roid_c = m.group(3)
        res_c = m.group(4)
        roid_e = m.group(5)
        res_e = m.group(6)

        m = re.search(
            r"""
        <tr><th[^>]*>Value</th><th[^>]*>Score</th></tr>\s*
        <tr><td[^>]*>(\d+)</td><td[^>]*>(\d+)</td></tr>\s*
        """,
            page,
            re.VERBOSE,
        )

        value = m.group(1)
        score = m.group(2)

        m = re.search(
            r"""
            <tr><th[^>]*>Agents</th><th[^>]*>Security\s+Guards</th></tr>\s*
            <tr><td[^>]*>([^<]+)</td><td[^>]*>([^<]+)</td></tr>\s*
        """,
            page,
            re.VERBOSE,
        )

        agents = m.group(1)
        guards = m.group(2)

        m = re.search(
            r"""
            <tr><th[^>]*>Light</th><th[^>]*>Medium</th><th[^>]*>Heavy</th></tr>\s*
            <tr><td[^>]*>([^<]+)</td><td[^>]*>([^<]+)</td><td[^>]*>([^<]+)</td></tr>
        """,
            page,
            re.VERBOSE,
        )

        factory_usage_light = m.group(1)
        factory_usage_medium = m.group(2)
        factory_usage_heavy = m.group(3)

        # atm the only span tag is the one around the hidden res.
        m = re.search(r"""<span[^>]*>(\d+)</span>""", page, re.VERBOSE)

        prod_res = m.group(1)

        query = "INSERT INTO planet (scan_id,roid_metal,roid_crystal,roid_eonium,res_metal,res_crystal,res_eonium,factory_usage_light,factory_usage_medium,factory_usage_heavy,prod_res,agents,guards)"
        query += " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        self.cursor.execute(
            query,
            (
                scan_id,
                roid_m,
                roid_c,
                roid_e,
                res_m,
                res_c,
                res_e,
                factory_usage_light,
                factory_usage_medium,
                factory_usage_heavy,
                prod_res,
                agents,
                guards,
            ),
        )
        # print("Planet: " + x + ":" + y + ":" + z)

    def parse_development(self, scan_id, page):
        # m = re.search('on (\d*)\:(\d*)\:(\d*) in tick (\d*)</th></tr><tr><td class="left">Light Factory</td><td>(\d*)</td></tr><tr><td class="left">Medium Factory</td><td>(\d*)</td></tr><tr><td class="left">Heavy Factory</td><td>(\d*)</td></tr><tr><td class="left">Wave Amplifier</td><td>(\d*)</td></tr><tr><td class="left">Wave Distorter</td><td>(\d*)</td></tr><tr><td class="left">Metal Refinery</td><td>(\d*)</td></tr><tr><td class="left">Crystal Refinery</td><td>(\d*)</td></tr><tr><td class="left">Eonium Refinery</td><td>(\d*)</td></tr><tr><td class="left">Research Laboratory</td><td>(\d*)</td></tr><tr><td class="left">Finance Centre</td><td>(\d*)</td></tr><tr><td class="left">Security Centre</td><td>(\d*)</td></tr>', page)
        m = re.search("on (\d*)\:(\d*)\:(\d*) in tick (\d*)</h2>", page)

        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        tick = m.group(4)

        m = re.search(
            """
            <tr><td[^>]*>Light\s+Factory</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Medium\s+Factory</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Heavy\s+Factory</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Wave\s+Amplifier</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Wave\s+Distorter</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Metal\s+Refinery</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Crystal\s+Refinery</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Eonium\s+Refinery</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Research\s+Laboratory</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Finance\s+Centre</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Military\s+Centre</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Security\s+Centre</td><td[^>]*>(\d*)</td></tr>\s*
            <tr><td[^>]*>Structure\s+Defence</td><td[^>]*>(\d*)</td></tr>\s*
            """,
            page,
            re.VERBOSE,
        )

        lightfactory = m.group(1)
        medfactory = m.group(2)
        heavyfactory = m.group(3)
        waveamp = m.group(4)
        wavedist = m.group(5)
        metalref = m.group(6)
        crystalref = m.group(7)
        eref = m.group(8)
        reslab = m.group(9)
        finance = m.group(10)
        military = m.group(11)
        security = m.group(12)
        structuredef = m.group(13)
        args = ()
        args += (
            scan_id,
            lightfactory,
            medfactory,
            heavyfactory,
            waveamp,
            wavedist,
            metalref,
            crystalref,
            eref,
            reslab,
            finance,
            military,
            security,
            structuredef,
        )

        m = re.search(
            """
        <tr><td[^>]*>Space\s+Travel</td><td[^>]*>(\d+)\s*<span[^>]*>[^<]*</span></td></tr>\s*
        <tr><td[^>]*>Infrastructure</td><td[^>]*>(\d+)\s*<span[^>]*>[^<]*</span></td></tr>\s*
        <tr><td[^>]*>Hulls</td><td[^>]*>(\d+)\s*<span[^>]*>[^<]*</span></td></tr>\s*
        <tr><td[^>]*>Waves</td><td[^>]*>(\d+)\s*<span[^>]*>[^<]*</span></td></tr>\s*
        <tr><td[^>]*>Core\s+Extraction</td><td[^>]*>(\d+)\s*<span[^>]*>[^<]*</span></td></tr>\s*
        <tr><td[^>]*>Covert\s+Ops</td><td[^>]*>(\d+)\s*<span[^>]*>[^<]*</span></td></tr>\s*
        <tr><td[^>]*>Asteroid\s+Mining</td><td[^>]*>(\d+)\s*<span[^>]*>[^<]*</span></td></tr>\s*
        <tr><td[^>]*>Population\s+Management</td><td[^>]*>(\d+)\s*<span[^>]*>[^<]*</span></td></tr>\s*
        """,
            page,
            re.VERBOSE,
        )

        travel = m.group(1)
        inf = m.group(2)
        hulls = m.group(3)
        waves = m.group(4)
        core = m.group(5)
        covop = m.group(6)
        mining = m.group(7)
        population = m.group(8)

        args += (travel, inf, hulls, waves, core, covop, mining, population)

        query = "INSERT INTO development (scan_id,light_factory,medium_factory,heavy_factory"
        query += ",wave_amplifier,wave_distorter,metal_refinery,crystal_refinery,eonium_refinery"
        query += ",research_lab,finance_centre,military_centre,security_centre,structure_defense"
        query += ",travel,infrastructure,hulls,waves,core,covert_op,mining,population)"
        query += " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        self.cursor.execute(query, args)
        # print("Development: " + x + ":" + y + ":" + z)

    def parse_incoming(self, _scan_id, page, _round):
        m = re.search("on (\d*)\:(\d*)\:(\d*) in tick (\d*)", page)
        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        tick = m.group(4)
        # No data from incoming scans is stored in the database
        # print("Incoming: %s:%s:%s from tick %s" % (
        #     x,
        #     y,
        #     z,
        #     tick,))

    def parse_unit(self, scan_id, page, table, round):
        m = re.search("on (\d*)\:(\d*)\:(\d*) in tick (\d*)", page)
        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        tick = m.group(4)

        for m in re.finditer(
            "(\w+\s?\w*\s?\w*)</td><td[^>]*>(\d+(?:,\d{3})*)</td>", page
        ):
            shipname = m.group(1)
            amount = m.group(2).replace(",", "")
            query  = "INSERT INTO %s" % (table,)
            query += " (scan_id,ship_id,amount)"
            query += " VALUES (%s,(SELECT id FROM ship WHERE name=%s AND round=%s),%s)"
            self.cursor.execute(query, (scan_id, shipname, round, amount,))
        # print("Unit: " + x + ":" + y + ":" + z)

    def parse_military(self, scan_id, page, table, round):
        m = re.search("on (\d*)\:(\d*)\:(\d*) in tick (\d*)", page)
        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        tick = m.group(4)

        # <tr><th class="left">Ship</th><th class="center">Base</th><th class="center">Fleet 1</th><th class="center">Fleet 2</th><th class="center">Fleet 3</th></tr>
        # <tr><td class="left">Moth</td><td class="center">0</td><td class="center">5,487</td><td class="center">0</td><td class="center">0</td></tr>
        # <tr><td class="left">Total Visible Ships</td><td class="center">0</td><td class="center">0</td><td class="center">0</td><td class="center">0</td></tr>
        # <tr><td class="left">Total Ships</td><td class="center">0</td><td class="center">0</td><td class="center">0</td><td class="center">0</td></tr>
        military_rows = 0
        military_arguments = []
        au_rows = 0
        au_arguments = []
        for m in re.finditer(
                "<tr><td[^>]*>([^<]+)</td><td[^>]*>([0-9,]+)</td><td[^>]*>([0-9,]+)</td><td[^>]*>([0-9,]+)</td><td[^>]*>([0-9,]+)</td></tr>",
                page):
            ship_name = m.group(1)
            if ship_name not in ['Ship', 'Total Visible Ships', 'Total Ships']:
                amounts = [
                    int(a.replace(',',
                                  '')) for a in [
                        m.group(2), # Base
                        m.group(3), # Fleet 1
                        m.group(4), # Fleet 2
                        m.group(5)  # Fleet 3
                    ]
                ]
                for fleet_index, amount in enumerate(amounts):
                    if amount > 0:
                        # print("%s %s in %s" % (
                        #     amount,
                        #     ship_name,
                        #     "base fleet" if fleet_index == 0 else "fleet %d" % (fleet_index,),
                        # ))
                        military_arguments += [
                            scan_id,
                            fleet_index,
                            ship_name,
                            round,
                            amount
                        ]
                        military_rows += 1

                au_arguments += [
                    scan_id,
                    ship_name,
                    round,
                    sum(amounts)
                ]
                au_rows += 1
        # Don't bother with scans that contain no ships of any kind.
        if military_rows > 0:
            military_query  = "INSERT INTO military (scan_id, fleet_index, ship_id, amount)"
            military_query += " VALUES "
            military_query += ", ".join(
                [
                    "(%s, %s, (SELECT id FROM ship WHERE name=%s AND round=%s), %s)"
                ] * military_rows
            )
            self.cursor.execute(military_query,
                                military_arguments)
        if au_rows > 0:
            # Also insert the data into the au table. This allows many commands
            # to only look in one place.
            au_query = "INSERT INTO au (scan_id, ship_id, amount)"
            au_query += " VALUES "
            au_query += ", ".join(
                [
                    "(%s, (SELECT id FROM ship WHERE name=%s AND round=%s), %s)"
                ] * au_rows
            )
            self.cursor.execute(au_query,
                                au_arguments)

        # print("Military: %s:%s:%s from tick %s" % (
        #     x,
        #     y,
        #     z,
        #     tick,))

    def parse_jumpgate(self, scan_id, page, round):
        m = re.search("on (\d+)\:(\d+)\:(\d+) in tick (\d+)", page)
        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        tick = m.group(4)
        # <td class=left>Origin</td><td class=left>Mission</td><td>Fleet</td><td>ETA</td><td>Fleetsize</td>
        # <td class=left>13:10:5</td><td class=left>Attack</td><td>Gamma</td><td>5</td><td>265</td>

        p = loadable.planet(x, y, z)
        # This fails if this planet exiled in this tick.
        if not p.load_most_recent(self.cursor, round):
            return

        # <td class="left">15:7:11</td><td class="left">Defend </td><td>Ad infinitum</td><td>9</td><td>0</td>
        # <tr><td class="left">10:4:9</td><td class="left">Return</td><td>They look thirsty</td><td>5</td><td>3000</td></tr>
        # <tr><td class="left">4:1:10</td><td class="left">Return</td><td>Or Is It?</td><td>9</td><td>3000</td></tr>
        # <tr><td class="left">10:1:10</td><td class="left">Defend</td><td class="left">Pesticide IV</td><td class="right">1</td><td class="right">0</td></tr>

        for m in re.finditer(
                "<td[^>]*><a[^>]*>(\d+)\:(\d+)\:(\d+)</a> \(<span[^>]*>[^<]*</span>\)</td><td[^>]*>([^<]+)</td><td[^>]*>([^<]+)</td><td[^>]*>(\d+)</td><td[^>]*>(\d+(?:,\d{3})*)</td>",
                page,
        ):
            originx = m.group(1)
            originy = m.group(2)
            originz = m.group(3)
            mission = m.group(4)
            fleet = m.group(5)
            eta = m.group(6)
            fleetsize = m.group(7).replace(",", "")

            origin = loadable.planet(originx, originy, originz)
            if origin.load_most_recent(self.cursor, round):
                query  = "INSERT INTO fleet (round, scan_id, owner_id, target, fleet_size, fleet_name, landing_tick, mission)"
                query += " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                query += " ON CONFLICT      (round,          owner_id, target,             fleet_name, landing_tick)"
                # The launch tick is not specified for incoming fleets on JGPs,
                # so don't update whatever might already be there.
                query += " DO UPDATE SET scan_id=EXCLUDED.scan_id, mission=EXCLUDED.mission, fleet_size=EXCLUDED.fleet_size"

                self.cursor.execute(
                    query,
                    (
                        round,
                        scan_id,
                        origin.id,
                        p.id,
                        fleetsize,
                        fleet,
                        int(tick) + int(eta),
                        mission.lower(),
                    ),
                )

        # print("Jumpgate: " + x + ":" + y + ":" + z)
