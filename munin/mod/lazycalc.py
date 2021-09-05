"""
Loadable.Loadable subclass
"""

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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

# Workaround incompatability between old robobrowser and new werkzeug
import werkzeug

werkzeug.cached_property = werkzeug.utils.cached_property

import re
import munin.loadable as loadable
from robobrowser import RoboBrowser
import threading
import datetime
import time
import operator


def timefunc(f):
    def f_timer(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        print(f.__name__, "took", end - start, "time")
        return result

    return f_timer


class lazycalc(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(
            r"^\s*(\d+)[. :-](\d+)[. :-](\d+)\s+(\d+)(?:\s+(skip))?"
        )
        self.usage = self.__class__.__name__ + " <x:y:z> <eta> [skip]"
        self.helptext = [
            'Builds a calc for your lazy ass. Add "skip" to ignore missing AU scans'
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        cur = self.config.getint("Planetarion", "current_round")
        if irc_msg.round != cur:
            irc_msg.reply(
                "I'm really sorry, but I can only make calcs for round %s. Fuckface."
                % (cur)
            )
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        x = m.group(1)
        y = m.group(2)
        z = m.group(3)
        eta = m.group(4)

        skip_missing = m.lastindex == 5

        target = loadable.planet(x=x, y=y, z=z)
        if not target.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply("No planet matching '%s:%s:%s' found" % (x, y, z))
            return 1

        jgp = self.get_jgp(target, irc_msg.round)
        if not jgp:
            irc_msg.reply(
                "I'd get right on that if I had a JGP from this tick. Really, I would. Right. On. That."
            )
            return 1

        planets = [row for row in jgp if row["eta"] == int(eta)]
        aus = self.get_aus(target, planets, irc_msg.round)
        outdated = [au for au in aus if au["age"] > 12]
        up_to_date = [au for au in aus if au["age"] <= 12]
        fleet_count = len(up_to_date)
        if len(outdated) > 0:
            if skip_missing:
                if fleet_count == 0:
                    irc_msg.reply("I need at least one AU to make a calc, dummy")
                    return 0
                else:
                    reply = "Ignoring missing AU scans on "
                    reply += ", ".join(
                        ["%s:%s:%s" % (p["x"], p["y"], p["z"]) for p in outdated]
                    )
                    if fleet_count > 10:
                        reply += ". This is going to take a moment, %s" % (
                            irc_msg.nick,
                        )
                    irc_msg.reply(reply)
            else:
                reply = ", ".join(
                    ["%s:%s:%s" % (p["x"], p["y"], p["z"]) for p in outdated]
                )
                irc_msg.reply(
                    "Get off your ass and give me fresh AUs on: %s" % (reply,)
                )
                return 1
        elif fleet_count > 10:
            irc_msg.reply("This is going to take a moment, %s" % (irc_msg.nick,))

        calc_creator(target, up_to_date, jgp, fleet_count, irc_msg).start()
        return 1

    @timefunc
    def get_jgp(self, p, round):
        query = (
            "SELECT DISTINCT ON (p.x, p.y, p.z, eta) p.x, p.y, p.z,"
            "       s.tick AS tick, s.nick, s.scantype, s.rand_id, s.scan_time,"
            "       f.mission, f.fleet_size, f.fleet_name, f.landing_tick-s.tick AS eta"
            " FROM       scan        AS s"
            " INNER JOIN fleet       AS f ON       s.id = f.scan_id"
            " INNER JOIN planet_dump AS p ON f.owner_id = p.id"
            " WHERE s.pid = %s"
            " AND f.mission IN ('defend', 'attack')"
            " AND p.tick = (SELECT max_tick(%s::smallint))"
            " AND p.round = %s"
            " AND s.id=(SELECT id FROM scan WHERE pid = s.pid"
            "           AND scantype = 'jgp'"
            "           AND s.tick = (SELECT max_tick(%s::smallint))"
            "           ORDER BY tick DESC, id DESC LIMIT 1)"
            " ORDER BY p.x ASC, p.y ASC, p.z ASC, eta ASC"
        )
        self.cursor.execute(query, (p.id, round, round, round))
        if self.cursor.rowcount < 1:
            return None
        return self.cursor.fetchall()

    def get_aus(self, target, planets, round):
        return [self.get_au(target.x, target.y, target.z, "defend", round)] + [
            self.get_au(p["x"], p["y"], p["z"], p["mission"], round) for p in planets
        ]

    @timefunc
    def get_au(self, x, y, z, mission, round):
        p = loadable.planet(x=x, y=y, z=z)
        base = {"x": x, "y": y, "z": z}
        if not p.load_most_recent(self.cursor, round):
            z = base.copy()
            val = z.update({"age": 1000})
            return val
        query = "SELECT max_tick(%s::smallint) - t1.tick AS age,t1.rand_id"
        query += " FROM scan AS t1"
        query += " WHERE t1.pid=%s"
        query += " AND scantype='au'"
        query += " ORDER BY tick DESC LIMIT 1"

        self.cursor.execute(query, (round, p.id,))
        if self.cursor.rowcount < 1:
            val = {"age": 1000}
        else:
            val = self.cursor.fetchone()
        res = dict(val)
        res["x"] = x
        res["y"] = y
        res["z"] = z
        res["mission"] = mission
        return res


class calc_creator(threading.Thread):
    def __init__(self, target, aus, jgp, fleet_count, irc_msg):
        self.target = target
        self.aus = aus
        self.jgp = jgp
        self.fleet_count = fleet_count
        self.irc_msg = irc_msg
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.unsafe_method()
        except Exception:
            self.irc_msg.reply(
                "Error in module '%s'. Please report the command you used to the bot owner as soon as possible."
                % (self.irc_msg.command_name,)
            )

    def unsafe_method(self):
        calc_url = self.create_calc(self.target, self.aus)
        self.irc_msg.reply(
            "Using ancient intel on %s:%s:%s from %s ago, I found %d fleet%s AND HERE'S YOUR GOD DAMNED CALC: %s"
            % (
                self.target.x,
                self.target.y,
                self.target.z,
                self.age(self.jgp),
                self.fleet_count,
                "s" if self.fleet_count > 1 else "",
                calc_url,
            )
        )

    def age(self, jgp):
        if len(jgp) > 0 and jgp[0]["scan_time"]:
            return str(datetime.datetime.utcnow() - jgp[0]["scan_time"])
        else:
            return "ages"

    @timefunc
    def create_calc(self, target, aus):
        browser = RoboBrowser(user_agent="a python robot", history=False)
        browser.open("https://game.planetarion.com/bcalc.pl")
        t = [
            a
            for a in aus
            if target.x == a["x"] and target.y == a["y"] and target.z == a["z"]
        ]
        if len(t) == 1:
            self.add_au(browser, t[0])
        for au in sorted(aus, key=operator.itemgetter("x", "y", "z")):
            if (
                len(t) != 1
                or target.x != au["x"]
                or target.y != au["y"]
                or target.z != au["z"]
            ):
                self.add_au(browser, au)
        form = browser.get_form()
        form["def_metal_asteroids"] = target.size
        form["action"] = "save"
        browser.submit_form(form)
        return browser.url

    @timefunc
    def add_au(self, browser, au):
        form = browser.get_form()
        form["scans_area"] = (
            "http://game.planetarion.com/showscan.pl?scan_id=" + au["rand_id"]
        )
        form["action"] = "add_att" if au["mission"] == "attack" else "add_def"
        browser.submit_form(form)
