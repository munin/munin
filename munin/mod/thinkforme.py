"""
Loadable subclass
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
import math
from munin import loadable


class thinkforme(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*((\d+)[.:\s-](\d+)[.:\s-](\d+))?(.*)")
        self.govre = re.compile(r"\s*\b(cor|dem|nat|soc|tot|ana)[a-z]*\b")
        self.numre = re.compile(r"\s*\b([0-9]+)\b")
        self.usage = self.__class__.__name__ + " [x:y:z] [government] [population on security] [target alert] [expected roids]"
        self.helptext = [
            "Get advice about whether to build refineries, FCs, or SCs. If no"
            " government is given, Totalitarianism is assumed. If no population"
            " is given, 40% is assumed. If no roids are given, current roid"
            " count is assumed. Arguments may be given in any order. The"
            " calculation takes into account remaining ticks, construction time,"
            " construction cost, guard wages, government ship production cost"
            " discount, and government alert bonus."
        ]
        self.max_scan_age = 48

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        if irc_msg.user == 'Dav':
            irc_msg.reply("Banned from %s" % (
                self.config.get("Connection", "nick"),
            ))
            return 0

        gov = 'tot'
        goal_alert = None
        population = 40
        size = None

        m = self.paramre.search(irc_msg.command_parameters)
        if m:
            if m.group(1):
                p = loadable.planet(x=m.group(2),
                                    y=m.group(3),
                                    z=m.group(4))
                if not p.load_most_recent(self.cursor, irc_msg.round):
                    irc_msg.reply("No planet matching '%s' found" % (m.group(1),))
                    return 1
            else:
                u = loadable.user(pnick=irc_msg.user)
                if u.load_from_db(self.cursor, irc_msg.round) and u.planet:
                    p = u.planet
                else:
                    irc_msg.reply(
                        "You must be registered to use the automatic %s command"
                        " (log in with Q and set mode +x, then make sure you've"
                        " set your planet with the pref command)" % (
                            self.__class__.__name__,
                        )
                    )
                    return 1
            for word in m.group(5).split():
                m = self.govre.search(word.lower())
                if m:
                    gov = m.group(1)
                else:
                    m = self.numre.search(word)
                    if m:
                        num = int(m.group(1))
                        if num > 100:
                            size = num
                        elif num > 50:
                            goal_alert = num
                        else:
                            population = num
                    else:
                        irc_msg.reply("Usage: %s" % (self.usage,))
                        return 1
        else:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 1

        result = self.calculate(p, goal_alert, population, gov, size, irc_msg)
        if result:
            irc_msg.reply(str(result))
            return 0
        else:
            return 1

    class result(object):
        def __init__(self, planet, goal_alert, population, government, size):
            self.planet     = planet
            self.goal_alert = goal_alert
            self.population = population
            self.government = government
            self.size = size

            self.best         = None
            self.guards       = None
            self.number       = 0
            self.first_income = None
            self.last_income  = None

        def __str__(self):
            string = "Planet %d:%d:%d should" % (
                self.planet.x,
                self.planet.y,
                self.planet.z,
            )
            if self.best:
                string += " build approximately an additional %d %ss" % (
                    self.number,
                    self.best,
                )
                string += " and employ %d total guards for %d alert with %d pop, %s, and %d roids (for %d" % (
                    self.guards,
                    self.goal_alert,
                    self.population,
                    self.government.title(),
                    self.size,
                    self.first_income,
                )
                if self.last_income is not None:
                    string += " -> %d" % (
                        self.last_income,
                    )
                string += "  fleet value per construction tick by round end)"
            else:
                string += " not build FCs, SCs, or Refs: they will not pay for themselves before round end"
            return string

    def calculate(self, planet, goal_alert, population, gov, size, irc_msg):
        governments = {
            "cor": "corporatism",
            "dem": "democracy",
            "nat": "nationalism",
            "soc": "socialism",
            "tot": "totalitarianism",
            "ana": "anarchy",
        }
        government = governments[gov] if gov in governments else "totalitarianism"
        # print("!thinkforme: Coords: %s:%s:%s, Government: %s, Population: %s, Goal alert: %s" % (
        #     p.x,
        #     p.y,
        #     p.z,
        #     government,
        #     population,
        #     goal_alert,
        # ))

        self.cursor.execute("SELECT max_tick(%s::smallint)", (
            irc_msg.round,
        ))
        tick = self.cursor.fetchone()["max_tick"]

        guards      = None
        planet_tick = None
        planet_id   = None
        query = """
        SELECT p.guards, s.tick, s.rand_id
        FROM scan AS s
        INNER JOIN planet AS p ON p.scan_id = s.id
        WHERE s.pid = %s
        AND s.tick >= %s
        ORDER BY scan_time DESC
        LIMIT 1;
        """
        self.cursor.execute(query, (
            planet.id,
            tick - self.max_scan_age,
        ))
        if self.cursor.rowcount == 1:
            row = self.cursor.fetchone()
            guards      = row["guards"]
            planet_tick = row["tick"]
            planet_id   = row["rand_id"]

        scs        = None
        refineries = None
        fcs        = None
        dev_tick   = None
        dev_id     = None
        query = """
        SELECT d.security_centre, d.finance_centre, d.metal_refinery, d.crystal_refinery, d.eonium_refinery, s.tick, s.rand_id
        FROM scan AS s
        INNER JOIN development AS d ON d.scan_id = s.id
        WHERE s.pid = %s
        AND s.tick >= %s
        ORDER BY scan_time DESC
        LIMIT 1;
        """
        self.cursor.execute(query, (
            planet.id,
            tick - self.max_scan_age,
        ))
        if self.cursor.rowcount == 1:
            row = self.cursor.fetchone()
            scs        = row["security_centre"]
            refineries = {
                'metal':   row["metal_refinery"],
                'crystal': row["crystal_refinery"],
                'eonium':  row["eonium_refinery"],
            }
            fcs        = row["finance_centre"]
            dev_tick   = row["tick"]
            dev_id     = row["rand_id"]

        if guards is None:
            if scs is None:
                irc_msg.reply("I need a recent planet and development scan")
                return None
            else:
                irc_msg.reply("I need a recent planet scan")
                return None
        elif scs is None:
            irc_msg.reply("I need a recent development scan")
            return None

        if size is None:
            size = planet.size

        gov_construction_speed = float(self.config.get("Planetarion", "%s_construction_speed" % (government,)))
        race_cu = int(self.config.get("Planetarion", "%s_construction_speed" % (planet.race,)))
        cons_speed = race_cu * (1.35 + gov_construction_speed)
        ref_cu = 750
        fc_cu = 1000
        sc_cu = 1000
        ref_build_time = ref_cu / cons_speed
        fc_build_time  =  fc_cu / cons_speed
        sc_build_time  =  sc_cu / cons_speed
        # print("!thinkforme: Race CU: %s | Gov CU speed: %s | Net CU/tick: %s | Ref time %.1f | FC time %.1f | SC time %.1f" % (
        #     race_cu,
        #     gov_construction_speed,
        #     cons_speed,
        #     ref_build_time,
        #     fc_build_time,
        #     sc_build_time,
        # ))

        gov_value_conversion = 100 - 100 * float(self.config.get("Planetarion", "%s_cost_reduction" % (government,)))
        gov_mining_bonus = float(self.config.get("Planetarion", "%s_mining_bonus" % (government,)))
        gov_alert_bonus = float(self.config.get("Planetarion", "%s_alert_bonus" % (government,)))

        r = self.result(planet, goal_alert, population, government, size)
        again = True
        # In each iteration of this loop, we calculate for which 'next
        # structure' the payoff is the highest, between it finishing and round
        # end. We then loop until the next structure to build is different to
        # the one we've been building so far, to avoid making the output look
        # too much like number soup.
        while again:
            min_ref = None
            if refineries["metal"] < min(refineries["crystal"], refineries["eonium"]):
                min_ref = 'metal'
            elif refineries["crystal"] < refineries["eonium"]:
                min_ref = "crystal"
            else:
                min_ref = 'eonium'
            refs = refineries[min_ref]
            fc_cost  = round(4500 * (( fcs + 1) ** 1.25 / 1000 + 1) * ( fcs + 1))
            ref_cost = round(3000 * ((refs + 1) ** 1.25 / 1000 + 1) * (refs + 1))
            sc_cost  = round(3000 * (( scs + 1) ** 1.25 / 1000 + 1) * ( scs + 1))

            ticks_left = 1177 - tick

            bonus = 0.25 + 0.005 * fcs + gov_mining_bonus
            unbuffed_income = 250 * size + 60000 + 1100 * (refineries['metal'] + refineries['crystal'] + refineries['eonium'])

            # If no explicit goal alertness is given, assume the planet's
            # current alertness is the goal.
            if r.goal_alert is None:
                r.goal_alert = int((50 + 5 * guards / (size + 1)) * (1.0 + population / 100.0 + 0.0275 * scs + gov_alert_bonus))
            # ...up to a maximum of 100, since going higher is wasteful.
            r.goal_alert = min(r.goal_alert,
                               100)
            def guards_needed(goal_alert,
                              scs,
                              gov_alert_speed,
                              roids):
                return max(
                    0,
                    math.ceil((goal_alert / (1.0 + population / 100.0 + 0.0275 * scs + gov_alert_bonus) - 50) / 5 * (roids + 1))
                )

            guards_with_current_scs = guards_needed(r.goal_alert,
                                                    scs,
                                                    gov_alert_bonus,
                                                    size)
            guards_with_one_more_sc = guards_needed(r.goal_alert,
                                                    scs + 1,
                                                    gov_alert_bonus,
                                                    size)
            extra_guards_without_sc = guards_with_current_scs - guards_with_one_more_sc

            ref_income = (1100 * (1 + bonus)           * (ticks_left - ref_build_time) - ref_cost) / gov_value_conversion
            fc_income  = (unbuffed_income * 0.005      * (ticks_left -  fc_build_time) -  fc_cost) / gov_value_conversion
            sc_income  = (extra_guards_without_sc * 12 * (ticks_left -  sc_build_time) -  sc_cost) / gov_value_conversion

            ref_income_per_cons_tick = round(ref_income * cons_speed / ref_cu)
            fc_income_per_cons_tick  = round( fc_income * cons_speed /  fc_cu)
            sc_income_per_cons_tick  = round( sc_income * cons_speed /  sc_cu)

            # print("!thinkforme: Refs: %s/%s/%s | Ref cost: %s | Ticks left: %.2f | Bonus %s | Ref build time: %.2f | Gov value conversion: %s | Net ref income: %s" % (
            #     refineries['metal'],
            #     refineries['crystal'],
            #     refineries['eonium'],
            #     ref_cost,
            #     ticks_left,
            #     bonus,
            #     ref_build_time,
            #     gov_value_conversion,
            #     ref_income_per_cons_tick,
            # ))
            # print("!thinkforme: FCs: %s | FC cost: %s | Ticks left: %.2f | FC build time: %.2f | Unbuffed income: %s | Gov value conversion: %s | Net FC income: %s" % (
            #     fcs,
            #     fc_cost,
            #     ticks_left,
            #     fc_build_time,
            #     unbuffed_income,
            #     gov_value_conversion,
            #     fc_income_per_cons_tick,
            # ))
            # print("!thinkforme: SCs: %s | SC cost: %s | Ticks left: %.2f | SC build time: %.2f | Goal alert: %s | Guards now: %s | Guards after extra SC: %s | Fireable guards: %s | Net SC income: %s" % (
            #     scs,
            #     sc_cost,
            #     ticks_left,
            #     sc_build_time,
            #     goal_alert,
            #     guards_with_current_scs,
            #     guards_with_one_more_sc,
            #     extra_guards_without_sc,
            #     sc_income_per_cons_tick,
            # ))
            # print("!thinkforme: ---NEXT---")

            # If building the next structure gives less value than it costs to
            # build, then don't bother.
            if (ref_income < ref_cost / gov_value_conversion and
                fc_income  <  fc_cost / gov_value_conversion and
                sc_income  <  sc_cost / gov_value_conversion):
                return r

            if sc_income_per_cons_tick > max(ref_income_per_cons_tick, fc_income_per_cons_tick):
                if r.best is None or r.best == 'SC':
                    r.best = 'SC'
                    r.number += 1
                    if r.number > 1:
                        r.last_income = sc_income_per_cons_tick
                    else:
                        r.first_income = sc_income_per_cons_tick
                    r.guards = guards_with_one_more_sc
                    scs += 1
                    tick += sc_build_time
                    # print("!thinkforme: %s:%s:%s | %s total SC for +%s value (%s guards) | Ref +%s | FC +%s (%s guards)" % (
                    #     planet.x,
                    #     planet.y,
                    #     planet.z,
                    #     scs,
                    #     sc_income_per_cons_tick,
                    #     guards_with_one_more_sc,
                    #     ref_income_per_cons_tick,
                    #     fc_income_per_cons_tick,
                    #     guards_with_current_scs
                    # ))
                else:
                    again = False
            elif ref_income_per_cons_tick > fc_income_per_cons_tick:
                if r.best is None or r.best == 'Ref':
                    r.best = 'Ref'
                    r.number += 1
                    tick += ref_build_time
                    if r.number > 1:
                        r.last_income = ref_income_per_cons_tick
                    else:
                        r.first_income = ref_income_per_cons_tick
                    r.guards = guards_with_current_scs
                    refineries[min_ref] += 1
                    # print("!thinkforme: %s:%s:%s | %s total Ref for +%s value (%s guards) | FC +%s | SC +%s (%s guards)" % (
                    #     planet.x,
                    #     planet.y,
                    #     planet.z,
                    #     refineries['metal'] + refineries['crystal'] + refineries['eonium'],
                    #     ref_income_per_cons_tick,
                    #     guards_with_current_scs,
                    #     fc_income_per_cons_tick,
                    #     sc_income_per_cons_tick,
                    #     guards_with_one_more_sc,
                    # ))
                else:
                    again = False
            else:
                if r.best is None or r.best == 'FC':
                    r.best = 'FC'
                    r.number += 1
                    tick += fc_build_time
                    if r.number > 1:
                        r.last_income = fc_income_per_cons_tick
                    else:
                        r.first_income = fc_income_per_cons_tick
                    r.guards = guards_with_current_scs
                    fcs += 1
                    # print("!thinkforme: %s:%s:%s | %s total FC for +%s value (%s guards) | Ref +%s | SC +%s (%s guards)" % (
                    #     planet.x,
                    #     planet.y,
                    #     planet.z,
                    #     fcs,
                    #     fc_income_per_cons_tick,
                    #     guards_with_current_scs,
                    #     ref_income_per_cons_tick,
                    #     sc_income_per_cons_tick,
                    #     guards_with_one_more_sc,
                    # ))
                else:
                    again = False

        return r
