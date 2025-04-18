"""
Loadable class
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

import re
import configparser
import datetime


class loadable(object):
    def __init__(self, cursor, level):
        self.cursor = cursor
        self.level = level
        self.coordre = re.compile(r"(\d+)[. :-](\d+)([. :-](\d+))?")
        self.planet_coordre = re.compile(r"(\d+)[. :-](\d+)[. :-](\d+)")
        self.idre = re.compile(r"([0-9A-Za-z]+)")
        self.helptext = None
        self.config = configparser.ConfigParser()
        if not self.config.read("muninrc"):
            raise ValueError(
                "Failed to read ./muninrc. Can not run without configuration"
            )

    def execute(self, user, access, irc_msg):
        print("Loadable execute")

    def aliases(self, command_text):
        comre = re.compile("^" + re.escape(command_text))
        m = comre.search(self.__class__.__name__)
        if m:
            return True
        return False

    def help(self, user, access, irc_msg):
        irc_msg.reply(self.usage)
        if hasattr(self, "helptext") and self.helptext:
            for h in self.helptext:
                irc_msg.reply(h)

    def cap(self, text):
        if len(text) > 3:
            return text.title()
        else:
            return text.upper()

    def format_value(self, cost):
        value = cost / 100
        suffixes = ['', 'k', 'm', 'b', 't']
        index = 0
        while value / 1000 > 9 and index < len(suffixes) - 1:
            value /= 1000
            index += 1
        result = ('%.1f' % (value,)).replace('.0', '');
        return '%s%s' % (result, suffixes[index],)

    def format_real_value(self, value):
        return self.format_value(value * 100)

    def split_opts(self, params):
        param_dict = {}
        for s in params.split():
            a = s.split("=")
            if len(a) != 2:
                return None
            param_dict[a[0].lower()] = a[1]
        return param_dict

    def human_readable_number_to_integer(self, number):
        suffixes = ['', 'k', 'm', 'b', 't']
        power = 0
        try:
            power = suffixes.index(number[-1].lower())
            return int(float(number[:-1]) * 1000 ** power)
        except:
            # int('1.2') fails, so pass it through float() first.
            return int(float(number))

    def current_tick(self, round):
        self.cursor.execute("SELECT max_tick(%s::smallint)", (round,))
        return self.cursor.fetchone()[0]

    def load_user_with_planet(self, pnick, irc_msg):
        u = self.load_user(pnick, irc_msg)
        if not u.planet:
            irc_msg.reply(
                "You must set your planet with the pref command for the "
                + self.__class__.__name__
                + " command to work"
            )
            return None
        return u

    def load_user(self, pnick, irc_msg, minimum_userlevel=-1):
        if not pnick:
            irc_msg.reply(
                "You must be registered to use the "
                + self.__class__.__name__
                + " command (log in with Q and set mode +x)"
            )
            return None
        u = self.load_user_from_pnick(pnick, irc_msg.round, minimum_userlevel=minimum_userlevel)
        if not u:
            irc_msg.reply(
                "You must be registered to use the automatic "
                + self.__class__.__name__
                + " command (log in with Q and set mode +x, then make sure you've set your planet with the pref command)"
            )
            return None
        return u

    def load_user_from_pnick(self, username, round, minimum_userlevel=-1):
        u = user(pnick=username, userlevel=minimum_userlevel)
        if u.load_from_db(self.cursor, round):
            return u
        else:
            return None

    def get_total_cons_from_scan(self, cursor, scan_id):
        query = "SELECT light_factory+medium_factory+heavy_factory+wave_amplifier+wave_distorter"
        query += "+metal_refinery+crystal_refinery+eonium_refinery+research_lab+military_centre+finance_centre+security_centre+structure_defense"
        query += " AS total FROM development"
        query += " WHERE id=%s"

        self.cursor.execute(query, (scan_id,))
        return self.cursor.fetchone()["total"]

    def pluralize(self, number, text):
        if number == 1:
            return text
        elif text.lower() in ['cookie', 'carebear', 'caretwink', 'day']:
            return text + "s"
        elif text.lower() == "match":
            return text + "es"
        return text

    def match_or_usage(self, irc_msg, needle, haystack):
        m = needle.search(haystack)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
        return m

    def command_not_used_in_home(self, irc_msg, command_name):
        if irc_msg.target.lower() != "#" + self.config.get("Auth", "home").lower():
            irc_msg.reply(
                "The %s command may only be used in #%s."
                % (
                    command_name,
                    self.config.get("Auth", "home"),
                )
            )
            return True
        False

    def phone_query_builder(self, u, query_filter=None, query_args=None):
        args = (u.id,)
        query = "SELECT pnick "
        query += " FROM phone AS t1"
        query += " INNER JOIN user_list AS t2"
        query += " ON t2.id=t1.user_id"
        query += " WHERE t1.user_id=%s"
        if query_filter:
            query += query_filter
            args += query_args

        self.cursor.execute(query, args)
        return self.cursor.fetchall()

    def get_ship_from_db(self, ship_name, round):
        query = "SELECT * FROM ship WHERE name ILIKE %s AND round=%s ORDER BY id"
        self.cursor.execute(query, (ship_name, round))
        ship = self.cursor.fetchone()

        if not ship:
            self.cursor.execute(
                query,
                (
                    "%" + ship_name + "%",
                    round,
                ),
            )
            ship = self.cursor.fetchone()

        if not ship and ship_name[-1].lower() == "s":
            ship_name = ship_name[0:-1]
            self.cursor.execute(
                query,
                (
                    "%" + ship_name + "%",
                    round,
                ),
            )
            ship = self.cursor.fetchone()
        return ship

    def is_nick_taken(self, nick):
        query = (
            "SELECT pnick"
            " FROM user_list"
            " WHERE pnick ilike %s"
            " OR alias_nick ilike %s"
            " LIMIT 1"
        )
        args = (nick, nick,)
        self.cursor.execute(query, args)
        return self.cursor.rowcount > 0


class defcall(object):
    def __init__(
        self,
        id=-1,
        bcalc=None,
        status=-1,
        claimed_by=None,
        comment=None,
        target=None,
        landing_tick=-1,
    ):
        self.id = id
        self.bcalc = bcalc
        self.status = status
        self.claimed_by = claimed_by
        self.comment = comment
        self.target = target
        self.landing_tick = landing_tick
        self.actual_target = None
        self.actual_owner = None
        self.actual_status = None

    def __str__(self):
        ret_str = "Defcall with id %s for %s:%s:%s landing %s" % (
            self.id,
            self.actual_target.x,
            self.actual_target.y,
            self.actual_target.z,
            self.landing_tick,
        )
        ret_str += " has status '%s' and was last modified by %s." % (
            self.actual_status,
            self.claimed_by or "no one",
        )
        ret_str += " It has"
        if self.bcalc:
            ret_str += " a"
        else:
            ret_str += " no"
        ret_str += " bcalc and has"
        if self.comment:
            ret_str += " a"
        else:
            ret_str += " no"
        ret_str += " comment."
        return ret_str

    def load_most_recent(self, cursor, round):
        # for now, always load from ID
        query = "SELECT id,bcalc,status,claimed_by,comment,target,landing_tick"
        query += " FROM defcalls WHERE id=%s"
        args = (self.id,)
        cursor.execute(query, args)
        d = cursor.fetchone()
        if not d:
            return 0
        self.bcalc = d["bcalc"]
        self.status = d["status"]
        self.claimed_by = d["claimed_by"]
        self.comment = d["comment"]
        self.target = d["target"]
        self.landing_tick = d["landing_tick"]
        p = planet(id=self.target)
        if not p.load_most_recent(cursor, round):
            raise Exception(
                "Defcall with id %s has no valid planet information. Oops..."
            )
        self.actual_target = p

        u = user(id=self.claimed_by)
        if not u.load_from_db(cursor):
            self.actual_owner = None
        self.actual_owner = u

        query = "SELECT status FROM defcall_status WHERE id = %s"
        cursor.execute(query, (self.status,))
        s = cursor.fetchone()
        self.actual_status = s["status"]

        return 1


class fleet(object):
    def __init__(
        self,
        id=-1,
        scan_id=-1,
        owner_id=-1,
        target_id=None,
        fleet_size=-1,
        fleet_name=None,
        launch_tick=-1,
        landing_tick=-1,
        mission=None,
        defcall=None,
    ):
        self.id = id
        self.scan_id = scan_id
        self.owner_id = owner_id
        self.target_id = target_id
        self.fleet_size = fleet_size
        self.fleet_name = fleet_name
        self.launch_tick = launch_tick
        self.landing_tick = landing_tick
        self.mission = mission
        self.defcall = defcall
        self.actual_target = None
        self.actual_owner = None
        self.actual_rand_id = None
        self.eta = -1

    def __str__(self):
        reply = "Fleet with id: %s from %s:%s:%s (%s)" % (
            self.id,
            self.actual_owner.x,
            self.actual_owner.y,
            self.actual_owner.z,
            self.actual_owner.race,
        )
        reply += " named '%s' with %s ships" % (self.fleet_name, self.fleet_size)
        reply += " headed for %s:%s:%s" % (
            self.actual_target.x,
            self.actual_target.y,
            self.actual_target.z,
        )

        reply += " with eta %s" % (self.eta,)
        if self.launch_tick:
            reply += " (%s)" % (self.landing_tick - self.launch_tick,)
        reply += " and mission %s" % (self.mission,)
        if self.defcall:
            reply += " as part of defcall id: %s" % (self.defcall.id,)
        return reply

    def load_most_recent(self, cursor, round):
        # for now, always load from ID
        query = "SELECT id,scan_id,owner_id,target,fleet_size,fleet_name"
        query += ",launch_tick,landing_tick, (landing_tick-(SELECT max_tick(%s::smallint))) AS eta,mission"
        query += " FROM fleet WHERE id=%s"
        args = (
            round,
            self.id,
        )
        cursor.execute(query, args)
        d = cursor.fetchone()
        if not d:
            return 0
        self.id = d["id"]
        self.scan_id = d["scan_id"]
        self.owner_id = d["owner_id"]
        self.target_id = d["target"]
        self.fleet_size = d["fleet_size"]
        self.fleet_name = d["fleet_name"]
        self.launch_tick = d["launch_tick"]
        self.landing_tick = d["landing_tick"]
        self.mission = d["mission"]
        self.eta = d["eta"]

        p = planet(id=self.target_id)
        if not p.load_most_recent(cursor, round):
            raise Exception(
                "Defcall with id %s has no valid target information. Oops..."
                % (self.id,)
            )
        self.actual_target = p

        p = planet(id=self.owner_id)
        if not p.load_most_recent(cursor, round):
            raise Exception(
                "Defcall with id %s has no valid owner information. Oops..."
                % (self.id,)
            )
        self.actual_owner = p

        query = "SELECT rand_id FROM scan WHERE id = %s"
        cursor.execute(query, (self.scan_id,))
        s = cursor.fetchone()
        if s:
            self.actual_rand_id = s["rand_id"]

        query = (
            "SELECT id FROM defcalls WHERE target=%s AND landing_tick=%s AND round=%s"
        )
        cursor.execute(
            query,
            (
                self.target_id,
                self.landing_tick,
                round,
            ),
        )
        s = cursor.fetchone()
        if s:
            defc = defcall(id=s["id"])
            if defc.load_most_recent(cursor, round):
                self.defcall = defc
        return 1


class planet(object):
    def __init__(
        self,
        x=-1,
        y=-1,
        z=-1,
        planetname=None,
        rulername=None,
        race=None,
        size=-1,
        score=-1,
        value=-1,
        id=-1,
        idle=-1,
    ):
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)
        self.rulername = rulername
        self.planetname = planetname
        self.race = race
        self.size = int(size)
        self.score = int(score)
        self.value = int(value)
        self.score_rank = -1
        self.value_rank = -1
        self.size_rank = -1
        self.xp = -1
        self.xp_rank = -1
        self.id = id
        self.idle = idle

    def __str__(self):
        retstr = "%s:%s:%s (%s) '%s' of '%s' " % (
            self.x,
            self.y,
            self.z,
            self.race,
            self.rulername,
            self.planetname,
        )
        retstr += "Score: %s (%s) " % (self.score, self.score_rank)
        retstr += "Value: %s (%s) " % (self.value, self.value_rank)
        retstr += "Size: %s (%s) " % (self.size, self.size_rank)
        retstr += "XP: %s (%s) " % (self.xp, self.xp_rank)
        retstr += "Idle: %s " % (self.idle,)
        return retstr

    def load_most_recent(self, cursor, round):
        p = {}
        if self.x > -1 and self.y > -1 and self.z > -1:
            # load from coords
            query = "SELECT x,y,z,planetname,rulername,race,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,idle,id"
            query += " FROM planet_dump WHERE round=%s AND x=%s AND y=%s AND z=%s AND tick=(SELECT max_tick(%s::smallint))"
            cursor.execute(
                query,
                (
                    round,
                    self.x,
                    self.y,
                    self.z,
                    round,
                ),
            )
        elif self.planetname and self.rulername:
            query = "SELECT x,y,z,planetname,rulername,race,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,idle,id"
            query += " FROM planet_dump WHERE round=%s AND planetname=%s AND rulername=%s AND tick=(SELECT max_tick(%s::smallint))"
            cursor.execute(
                query,
                (
                    round,
                    self.planetname,
                    self.rulername,
                    round,
                ),
            )
        elif self.id and self.id > 0:
            query = "SELECT x,y,z,planetname,rulername,race,size,score,value,score_rank,value_rank,size_rank,xp,xp_rank,idle,id"
            query += " FROM planet_dump WHERE round=%s AND id=%s AND tick=(SELECT max_tick(%s::smallint))"
            cursor.execute(
                query,
                (
                    round,
                    self.id,
                    round,
                ),
            )
        else:
            raise Exception("Tried to load planet with no unique identifiers")
        p = cursor.fetchone()
        if not p:
            return None
        self.x = p["x"]
        self.y = p["y"]
        self.z = p["z"]
        self.rulername = p["rulername"]
        self.planetname = p["planetname"]
        self.race = p["race"]
        self.size = p["size"]
        self.score = p["score"]
        self.value = p["value"]
        self.score_rank = p["score_rank"]
        self.value_rank = p["value_rank"]
        self.size_rank = p["size_rank"]
        self.xp = p["xp"]
        self.xp_rank = p["xp_rank"]
        self.idle = p["idle"]
        self.id = p["id"]
        return 1

    def calc_xp(self, victim, mcs, fleet_admiral_bonus):
        cap = self.cap_rate(victim) * victim.size
        bravery_factor = self.bravery(victim)
        war_bonus = self.war_xp_bonus(victim)
        mc_bonus = 0.005 * float(mcs)

        def inner_xp_calc(round_factor, fleet_admiral_bonus):
            raw_xp = cap * 5 * bravery_factor * round_factor * (1 + fleet_admiral_bonus / 100.0) * (1 + war_bonus + mc_bonus)
            return int(min(self.score / 180.0,
                           raw_xp * (0.95 ** ((self.xp + raw_xp * 1.5) / 10000.0)) * min(1.25,
                                                                                         max(0.1,
                                                                                             1.5 - self.xp / 200000.0) + min(0.2,
                                                                                                                             (war_bonus + mc_bonus) * 0.003))))

        # Round factor is determined by UNIVERSE land rate over the last 168
        # ticks. The actual formula to calculate this number is:
        #
        #     round_factor = max(min(2.4 - 2 * landed / launched,
        #                            2),
        #                        1)
        #
        # However, since we don't know what the inputs should be, we calculate
        # XP twice, using the minimum and maximum round factor (1 and 2).
        min_round_factor = 1.0 # 70%+ of launched attack fleets lands.
        max_round_factor = 2.0 # 20%- of launched attack fleets lands.

        # Each fleet has an admiral that /supposedly/ gives between 0% and 30%
        # increase in XP.
        min_fleet_admiral_bonus = 0
        max_fleet_admiral_bonus = 30
        if fleet_admiral_bonus is not None:
            min_fleet_admiral_bonus = fleet_admiral_bonus
            max_fleet_admiral_bonus = fleet_admiral_bonus
        # Note that the above description is inaccurate, despite the fact that
        # it's lifted straight from the manual: since the bonus is used in both
        # the base and exponent of the calculation, the actual range can be
        # much larger. The Planetarion bcalc implements this incorrectly,
        # simply taking the XP gain with 0% fleet admiral bonus, and increasing
        # it by 30% to get the maximum. I am not sure if the combat engine
        # makes the same mistake.

        return (
            inner_xp_calc(min_round_factor, min_fleet_admiral_bonus),
            inner_xp_calc(max_round_factor, max_fleet_admiral_bonus),
        )

    def war_xp_bonus(self, victim):
        # If this planet's alliance is at war with the target's alliance, you
        # get more XP. If another alliance was already at war with them when
        # yours declared war, the XP bonus is halved.
        return 0.0  # TODO:

    def bravery(self, victim):
        return min(2.0,
                   max(0.2,
                       min(2.25,
                           float(victim.score) / float(self.score)) - 0.25) * max(0.2,
                                                                                  min(2.25,
                                                                                      float(victim.value) / float(self.value)) - 0.25))

    def cap_rate(self, victim, war_bonus=0.0):
        max_cap_rate = 0.25 + war_bonus
        modifier = (float(victim.value) / float(self.value)) ** 0.5
        return max(0.15,
                   min(max_cap_rate * modifier,
                       max_cap_rate))

    def vdiff(self, cursor, tick, round):
        query = (
            "SELECT value FROM planet_dump AS t1 WHERE tick=%s AND id=%s AND round=%s"
        )
        cursor.execute(query, (tick, self.id, round))
        if cursor.rowcount > 0:
            old_value = cursor.fetchone()["value"]
            return self.value - old_value
        else:
            return None

    def resources_per_agent(self, target):
        return min(10000, (target.value * 2000) / self.value)


class galaxy(object):
    def __init__(self, x=-1, y=-1, name=None, size=-1, score=-1, value=-1, id=-1):
        self.x = int(x)
        self.y = int(y)
        self.name = name
        self.size = int(size)
        self.score = int(score)
        self.value = int(value)
        self.score_rank = -1
        self.value_rank = -1
        self.size_rank = -1
        self.xp = -1
        self.xp_rank = -1
        self.id = id
        self.members = -1

    def __str__(self):
        retstr = "%s:%s '%s' Members: %s " % (self.x, self.y, self.name, self.members)
        retstr += "Score: %s (%s) " % (self.score, self.score_rank)
        retstr += "Value: %s (%s) " % (self.value, self.value_rank)
        retstr += "Size: %s (%s) " % (self.size, self.size_rank)
        retstr += "XP: %s (%s) " % (self.xp, self.xp_rank)
        return retstr

    def load_most_recent(self, cursor, round):
        g = {}
        if self.x > 0 and self.y > 0:
            # load from coords
            query  = "SELECT g.x,g.y,g.name,g.size,g.score,g.value,g.score_rank,g.value_rank,g.size_rank,g.xp,g.xp_rank,g.id,COUNT(p.x) AS members "
            query += "FROM galaxy_dump AS g "
            query += "INNER JOIN planet_dump AS p "
            query += "ON p.round = g.round AND p.tick = g.tick AND p.x = g.x AND p.y = g.y "
            query += "WHERE g.round = %s "
            query += "AND g.tick=(SELECT max_tick(%s::smallint)) "
            query += "AND g.x = %s "
            query += "AND g.y = %s "
            query += "GROUP BY g.x,g.y,g.name,g.size,g.score,g.value,g.score_rank,g.value_rank,g.size_rank,g.xp,g.xp_rank,g.id;"
            cursor.execute(
                query,
                (
                    round,
                    round,
                    self.x,
                    self.y,
                ),
            )
        else:
            raise Exception("Tried to load planet with no unique identifiers")
        g = cursor.fetchone()
        if not g:
            return None
        self.x = g["x"]
        self.y = g["y"]
        self.name = g["name"]
        self.size = g["size"]
        self.score = g["score"]
        self.value = g["value"]
        self.score_rank = g["score_rank"]
        self.value_rank = g["value_rank"]
        self.size_rank = g["size_rank"]
        self.xp = g["xp"]
        self.xp_rank = g["xp_rank"]
        self.id = g["id"]
        self.members = g["members"]
        return 1


class alliance(object):
    def __init__(
        self, score_rank=-1, name=None, size=-1, members=-1, score=-1, id=None
    ):
        self.score_rank = int(score_rank)
        self.name = name
        self.size = int(size)
        self.members = int(members)
        self.score = int(score)
        self.size_rank = -1
        self.members_rank = -1
        self.score_avg = -1
        self.size_avg = -1
        self.score_avg_rank = -1
        self.size_avg_rank = -1

        self.id = id

    def __str__(self):
        retstr = "'%s' Members: %s (%s) " % (self.name, self.members, self.members_rank)
        retstr += "Score: %s (%s) Avg: %s (%s) " % (
            self.score,
            self.score_rank,
            self.score_avg,
            self.score_avg_rank,
        )
        retstr += "Size: %s (%s) Avg: %s (%s) " % (
            self.size,
            self.size_rank,
            self.size_avg,
            self.size_avg_rank,
        )
        retstr += "Value: %s (%s) Avg: %s (%s)" % (
            self.value,
            self.value_rank,
            self.value_avg,
            self.value_avg_rank,
        )
        return retstr

    def load_most_recent(self, cursor, round):
        a = {}
        if self.name:
            # load from exact name
            query = "SELECT name,size,members,score,size_rank,members_rank,score_rank,score_avg,size_avg,score_avg_rank,size_avg_rank,id, total_value,total_value_rank,total_value_avg,total_value_avg_rank"
            query += " FROM alliance_dump WHERE round=%s AND name ILIKE %s AND tick=(SELECT max_tick(%s::smallint))"
            cursor.execute(
                query,
                (
                    round,
                    self.name,
                    round,
                ),
            )

            # if that doesn't work, load from fuzzy name
            if cursor.rowcount < 1:
                cursor.execute(
                    query,
                    (
                        round,
                        "%" + self.name + "%",
                        round,
                    ),
                )
        else:
            raise Exception("Tried to load alliance with no unique identifiers")
        a = cursor.fetchone()
        if not a:
            return None
        self.name = a["name"]
        self.size = a["size"]
        self.score = a["score"]
        self.score_rank = a["score_rank"]
        self.size_rank = a["size_rank"]
        self.members = a["members"]
        self.members_rank = a["members_rank"]
        self.score_avg = a["score_avg"]
        self.size_avg = a["size_avg"]
        self.score_avg_rank = a["score_avg_rank"]
        self.size_avg_rank = a["size_avg_rank"]
        self.id = a["id"]
        self.value = a["total_value"]
        self.value_rank = a["total_value_rank"]
        self.value_avg = a["total_value_avg"]
        self.value_avg_rank = a["total_value_avg_rank"]
        return 1


class user(object):
    def __init__(
        self,
        id=-1,
        pnick=None,
        sponsor=None,
        userlevel=-1,
        planet_id=-1,
        phone=None,
        pubphone=False,
        stay=False,
        invites=-1,
        available_cookies=-1,
        last_cookie_date=None,
        carebears=-1,
        fleetcount=-1,
        fleetcomment=None,
        fleetupdated=-1,
        alias_nick=None,
    ):
        self.id = id
        # Allow people to use use nick prefixes on Slack, Telegram, etc.
        self.pnick = pnick.removeprefix('@')
        self.sponsor = sponsor
        self.userlevel = userlevel
        self.planet_id = planet_id
        self.planet = None
        self.phone = phone
        self.pubphone = pubphone
        self.stay = stay
        self.pref = False
        self.available_cookies = -1
        self.last_cookie_date = None
        self.invites = -1
        self.carebears = carebears
        self.fleetcount = fleetcount
        self.fleetcomment = fleetcomment
        self.fleetupdated = fleetupdated
        self.alias_nick = alias_nick
        self.lemming = False

    @staticmethod
    def count_members(cursor):
        query = "SELECT count(*) as count FROM user_list WHERE userlevel >= 100"
        cursor.execute(query)
        return cursor.fetchone()["count"]

    def lookup_query(self):
        query = "SELECT id, pnick, sponsor, userlevel, phone, pubphone, invites, available_cookies, last_cookie_date, carebears, alias_nick"
        query += " FROM user_list WHERE "
        return query

    def lookup_round_query(self):
        query = (
            "SELECT planet_id, stay, fleetcount, fleetcomment, fleetupdated, lemming "
        )
        query += " FROM round_user_pref AS p"
        query += " WHERE p.round=%s AND p.user_id=%s"
        return query

    def load_from_db(self, cursor, round=None):
        query = self.lookup_query()
        if self.id and self.id > 0:
            query += " id=%s"
            cursor.execute(query, (self.id,))
        elif self.pnick:
            query += " ( pnick ILIKE %s OR alias_nick ILIKE %s ) AND userlevel >= %s"
            cursor.execute(query, (self.pnick, self.pnick, self.userlevel))
        else:
            return None
        u = cursor.fetchone()
        if self.pnick and not u:
            partial_nick = "%" + self.pnick + "%"
            query = self.lookup_query()
            query += " pnick ILIKE %s OR alias_nick ILIKE %s"
            query += " ORDER BY userlevel DESC"
            cursor.execute(
                query,
                (
                    partial_nick,
                    partial_nick,
                ),
            )
            u = cursor.fetchone()
        if u:
            self.id = u["id"]
            self.pnick = u["pnick"]
            self.sponsor = u["sponsor"]
            self.userlevel = u["userlevel"]
            self.phone = u["phone"]
            self.pubphone = u["pubphone"]
            self.pref = True
            self.invites = u["invites"]
            self.available_cookies = u["available_cookies"]
            self.last_cookie_date = u["last_cookie_date"]
            self.carebears = u["carebears"]
            self.alias_nick = u["alias_nick"]

            if round:
                query = self.lookup_round_query()
                cursor.execute(
                    query,
                    (
                        round,
                        u["id"],
                    ),
                )
                if cursor.rowcount > 0:
                    u = cursor.fetchone()
                    if u:
                        self.planet_id = u["planet_id"]
                        if self.planet_id:
                            self.planet = planet(id=self.planet_id)
                            self.planet.load_most_recent(cursor, (round,))
                        else:
                            self.planet = None
                        self.stay = u["stay"]
                        self.fleetcount = u["fleetcount"]
                        self.fleetcomment = u["fleetcomment"]
                        self.fleetupdated = u["fleetupdated"]
                        self.lemming = u["lemming"]
            return 1
        return None

    def munin_number(self, cursor, config):
        if self.sponsor.lower() == config.get("Connection", "nick").lower():
            return 1
        u = user(pnick=self.sponsor)
        if (
            u.load_from_db(cursor)
            and u.userlevel >= 100
            and u.pnick.lower() != u.sponsor.lower()
        ):
            parent_number = u.munin_number(cursor, config)
            if parent_number:
                return parent_number + 1

    def get_fleets(self, cursor, round):
        query = "SELECT t1.ship, t1.ship_count"
        query += " FROM user_fleet AS t1 "
        query += " WHERE t1.user_id=%s AND t1.round=%s"
        cursor.execute(
            query,
            (
                self.id,
                round,
            ),
        )
        return cursor.fetchall()

    def check_available_cookies(self, cursor, config):
        now = datetime.datetime.now()
        now = datetime.datetime(now.year, now.month, now.day)
        if not self.last_cookie_date or (now - self.last_cookie_date).days > 0:
            self.available_cookies = int(config.get("Alliance", "cookies_per_day"))
            query = "UPDATE user_list SET available_cookies = %s,last_cookie_date = %s WHERE id = %s"
            cursor.execute(query, (self.available_cookies, now, self.id))
        return self.available_cookies

    def has_ancestor(self, cursor, possible_ancestor, round):
        ancestor = user(pnick=self.sponsor)
        if ancestor.load_from_db(cursor, round):
            if ancestor.pnick.lower() == possible_ancestor.lower():
                return True
            else:
                return ancestor.has_ancestor(cursor, possible_ancestor, round)
        return False


class intel(object):
    def __init__(
        self,
        id=None,
        pid=-1,
        nick=None,
        gov=None,
        bg=None,
        covop=False,
        defwhore=False,
        fakenick=None,
        alliance=None,
        reportchan=None,
        scanner=False,
        distwhore=False,
        relay=False,
        comment=None,
    ):
        self.id = id
        self.pid = pid
        self.nick = nick
        self.gov = gov
        self.covop = covop
        self.bg = bg
        self.defwhore = defwhore
        self.fakenick = fakenick
        self.alliance = alliance
        self.reportchan = reportchan
        self.relay = relay
        self.scanner = scanner
        self.distwhore = distwhore
        self.comment = comment

    def load_from_db(self, cursor, round):
        query = "SELECT i.id AS id,pid,nick,defwhore,gov,covop,bg,fakenick,relay,reportchan,scanner,distwhore,comment,a.name AS alliance"
        query += " FROM intel AS i"
        query += " LEFT JOIN alliance_canon AS a ON i.alliance_id=a.id "
        query += " WHERE i.round=%s AND "
        if self.id and self.id > 0:
            query += "id=%s"
            cursor.execute(
                query,
                (
                    round,
                    self.id,
                ),
            )
        elif self.pid > 0:
            query += "pid=%s"
            cursor.execute(
                query,
                (
                    round,
                    self.pid,
                ),
            )
        elif self.nick:
            query += "nick=%s LIMIT 1"
            cursor.execute(
                query,
                (
                    round,
                    "%" + self.nick + "%",
                ),
            )
        elif self.fakenick:
            query += "fakenick=%s LIMIT 1"
            cursor.execute(
                query,
                (
                    round,
                    "%" + self.fakenick + "%",
                ),
            )
        elif self.comment:
            query += "comment=%s LIMIT 1"
            cursor.execute(
                query,
                (
                    round,
                    "%" + self.comment + "%",
                ),
            )
        i = cursor.fetchone()
        if not i:
            return None
        self.id = i["id"]
        self.pid = i["pid"]
        self.nick = i["nick"]
        self.gov = i["gov"]
        self.defwhore = i["defwhore"] and True or False
        self.bg = i["bg"]
        self.covop = i["covop"] and True or False
        self.fakenick = i["fakenick"]
        self.alliance = i["alliance"]
        self.reportchan = i["reportchan"]
        self.relay = i["relay"] and True or False
        self.scanner = bool(i["scanner"]) and True or False
        self.distwhore = bool(i["distwhore"]) and True or False
        self.comment = i["comment"]
        return 1

    def __str__(self):
        retlist = []
        if self.nick:
            retlist.append("nick=%s" % (self.nick,))
        if self.fakenick:
            retlist.append("fakenick=%s" % (self.fakenick,))
        if self.gov:
            retlist.append("gov=%s" % (self.gov,))
        if self.defwhore:
            retlist.append("defwhore=%s" % (self.defwhore,))
        if self.bg:
            retlist.append("bg=%s" % (self.bg,))
        if self.covop:
            retlist.append("covop=%s" % (self.covop,))
        if self.alliance:
            retlist.append("alliance=%s" % (self.alliance,))
        if self.relay:
            retlist.append("relay=%s" % (self.relay,))
        if self.reportchan:
            retlist.append("reportchan=%s" % (self.reportchan,))
        if self.scanner:
            retlist.append("scanner=%s" % (self.scanner,))
        if self.distwhore:
            retlist.append("distwhore=%s" % (self.distwhore,))
        if self.comment:
            retlist.append("comment=%s" % (self.comment,))

        return " ".join(retlist)

    def change_list(self):
        retlist = []
        if self.nick:
            retlist.append("nick=%s")
        if self.fakenick:
            retlist.append("fakenick=%s")
        if self.gov:
            retlist.append("gov=%s")
        if self.defwhore:
            retlist.append("defwhore=%s")
        if self.bg:
            retlist.append("bg=%s")
        if self.covop:
            retlist.append("covop=%s")
        if self.alliance:
            retlist.append("alliance=%s")
        if self.relay:
            retlist.append("relay=%s")
        if self.reportchan:
            retlist.append("reportchan=%s")
        if self.scanner:
            retlist.append("scanner=%s")
        if self.distwhore:
            retlist.append("distwhore=%s")
        if self.comment:
            retlist.append("comment=%s")

        return " ".join(retlist)

    def change_tuple(self):
        rettup = ()
        if self.nick:
            rettup += (self.nick,)
        if self.fakenick:
            rettup += (self.fakenick,)
        if self.gov:
            rettup += (self.gov,)
        if self.defwhore:
            rettup += (self.defwhore,)
        if self.bg:
            rettup += (self.bg,)
        if self.covop:
            rettup += (self.covop,)
        if self.alliance:
            rettup += (self.alliance,)
        if self.relay:
            rettup += (self.relay,)
        if self.reportchan:
            rettup += (self.reportchan,)
        if self.scanner:
            rettup += (self.scanner,)
        if self.distwhore:
            rettup += (self.distwhore,)
        if self.comment:
            rettup += (self.comment,)

        return rettup

    def is_empty(self):

        if self.nick:
            return 0
        if self.fakenick:
            return 0
        if self.bg:
            return 0
        if self.defwhore:
            return 0
        if self.gov:
            return 0
        if self.covop:
            return 0
        if self.alliance:
            return 0
        if self.relay:
            return 0
        if self.reportchan:
            return 0
        if self.scanner:
            return 0
        if self.distwhore:
            return 0
        if self.comment:
            return 0
        return 1


class booking(object):
    def __init__(self, id=-1, pnick=None, nick=None, tick=-1, pid=-1, uid=-1):
        self.id = id
        self.pnick = pnick
        self.nick = nick
        self.tick = tick
        self.pid = pid
        self.uid = uid

    def load_from_db(self, cursor, round):
        query = "SELECT t1.id AS id, t1.nick AS nick, t1.pid AS pid, t1.tick AS tick, t1.uid AS uid FROM target AS t1 WHERE round=%s AND"

        if self.tick and self.pid:
            query += "pid=%s AND tick=%s "
            cursor.execute(
                query,
                (
                    round,
                    self.pnick,
                ),
            )
            b = cursor.fetchone()
            if not b:
                return None
            self.id = b["id"]
            self.pnick = b["pnick"]
            self.nick = b["nick"]
            self.tick = b["tick"]
            self.pid = b["pid"]
            self.uid = b["uid"]
            return 1
        else:
            return None
        return None
