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
        self.usage = self.__class__.__name__ + " [x:y:z] [government] [population on security] [target alert]"
        self.helptext = [
            "Get advice about whether to build refineries, FCs, or SCs. If no"
            " government is given, Totalitarianism is assumed. If no population"
            " is given, 40% is assumed. Arguments may be given in any order."
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

        m = self.paramre.search(irc_msg.command_parameters)
        if m:
            if m.group(1):
                irc_msg.reply("1 %s, 2 %s, 3 %s, 4 %s, 5 %s" % (
                    m.group(1),
                    m.group(2),
                    m.group(3),
                    m.group(4),
                    m.group(5),
                ))
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
                        if num > 50:
                            goal_alert = num
                        else:
                            population = num
                    else:
                        irc_msg.reply("Usage: %s" % (self.usage,))
                        return 1
        else:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 1

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
            p.id,
            tick - self.max_scan_age,
        ))
        if self.cursor.rowcount == 1:
            row = self.cursor.fetchone()
            guards      = row["guards"]
            planet_tick = row["tick"]
            planet_id   = row["rand_id"]

        scs      = None
        mrefs    = None
        crefs    = None
        erefs    = None
        fcs      = None
        dev_tick = None
        dev_id   = None
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
            p.id,
            tick - self.max_scan_age,
        ))
        if self.cursor.rowcount == 1:
            row = self.cursor.fetchone()
            scs      = row["security_centre"]
            mrefs    = row["metal_refinery"]
            crefs    = row["crystal_refinery"]
            erefs    = row["eonium_refinery"]
            fcs      = row["finance_centre"]
            dev_tick = row["tick"]
            dev_id   = row["rand_id"]

        if guards is None:
            if scs is None:
                irc_msg.reply("I need a recent planet and development scan")
                return 1
            else:
                irc_msg.reply("I need a recent planet scan")
                return 1
        elif scs is None:
            irc_msg.reply("I need a recent development scan")
            return 1

        refs = min(
            row["metal_refinery"],
            row["crystal_refinery"],
            row["eonium_refinery"]
        )
        fc_cost =  round(4500 * (( fcs + 1) ** 1.25 / 1000 + 1) * ( fcs + 1))
        ref_cost = round(3000 * ((refs + 1) ** 1.25 / 1000 + 1) * (refs + 1))
        # If your government is Totalitarianism with 11 SCs and 121 guards, you
        # have ever so slightly over 94 alert. Adding 1 more SC means you need
        # 0 guards to also have 94 alert, making this a convenient test case.
        #
        # scs = 11
        # guards = 121
        sc_cost =  round(3000 * (( scs + 1) ** 1.25 / 1000 + 1) * ( scs + 1))

        ticks_left = 1177 - tick

        gov_construction_speed = float(self.config.get("Planetarion", "%s_construction_speed" % (government,)))
        race_cu = int(self.config.get("Planetarion", "%s_construction_speed" % (p.race,)))
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
        bonus = 0.25 + 0.005 * fcs + gov_mining_bonus
        unbuffed_income = 250 * p.size + 60000 + 1100 * (mrefs + crefs + erefs)

        gov_alert_bonus = float(self.config.get("Planetarion", "%s_alert_bonus" % (government,)))
        if goal_alert is None:
            goal_alert = int((50 + 5 * guards / (p.size + 1)) * (1.0 + population / 100.0 + 0.0275 * scs + gov_alert_bonus))
        def guards_needed(goal_alert,
                          scs,
                          gov_alert_speed,
                          roids):
            return max(
                0,
                math.ceil((goal_alert / (1.0 + population / 100.0 + 0.0275 * scs + gov_alert_bonus) - 50) / 5 * (roids + 1))
            )

        guards_with_current_scs = guards_needed(goal_alert,
                                                scs,
                                                gov_alert_bonus,
                                                p.size)
        guards_with_one_more_sc = guards_needed(goal_alert,
                                                scs + 1,
                                                gov_alert_bonus,
                                                p.size)
        extra_guards_without_sc = guards_with_current_scs - guards_with_one_more_sc

        ref_income = round(((1100 * (1 + bonus)           * (ticks_left - ref_build_time) - ref_cost) / gov_value_conversion) * cons_speed / ref_cu)
        fc_income  = round(((unbuffed_income * 0.005      * (ticks_left -  fc_build_time) -  fc_cost) / gov_value_conversion) * cons_speed /  fc_cu)
        sc_income  = round(((extra_guards_without_sc * 12 * (ticks_left -  sc_build_time) -  sc_cost) / gov_value_conversion) * cons_speed /  sc_cu)

        # print("!thinkforme: Refs: %s/%s/%s | Min refs: %s | Ref cost: %s | Ticks left: %s | Bonus %s | Ref build time: %s | Gov value conversion: %s | Net ref income: %s" % (
        #     mrefs,
        #     crefs,
        #     erefs,
        #     refs,
        #     ref_cost,
        #     ticks_left,
        #     bonus,
        #     ref_build_time,
        #     gov_value_conversion,
        #     ref_income,
        # ))
        # print("!thinkforme: FCs: %s | FC cost: %s | Ticks left: %s | FC build time: %s | Unbuffed income: %s | Gov value conversion: %s | Net FC income: %s" % (
        #     fcs,
        #     fc_cost,
        #     ticks_left,
        #     fc_build_time,
        #     unbuffed_income,
        #     gov_value_conversion,
        #     fc_income,
        # ))
        # print("!thinkforme: SCs: %s | SC cost: %s | Ticks left: %s | SC build time: %s | Alert: %s | Guards now: %s | Guards after extra SC: %s | Fireable guards: %s | Net SC income: %s" % (
        #     scs,
        #     sc_cost,
        #     ticks_left,
        #     sc_build_time,
        #     alert,
        #     guards_with_current_scs,
        #     guards_with_one_more_sc,
        #     extra_guards_without_sc,
        #     sc_income,
        # ))

        if sc_income > max(ref_income, fc_income):
            best            = ["n SC", "Ref", "FC"]
            best_income     = [sc_income, ref_income, fc_income]
            best_guards     = [guards_with_one_more_sc, guards_with_current_scs]
        else:
            best_guards     = [guards_with_current_scs, guards_with_one_more_sc]
            if ref_income > fc_income:
                best            = [" Refinery", "FC", "SC"]
                best_income     = [ref_income, fc_income, sc_income]
            else:
                best            = ["n FC", "Ref", "SC"]
                best_income     = [fc_income, ref_income, sc_income]

        reply = "Planet %d:%d:%d should build a" % (
            p.x,
            p.y,
            p.z,
        )
        reply += "%s and hire %d guards for %d alert with %d pop!" % (
            best[0],
            best_guards[0],
            goal_alert,
            population,
        )
        reply += " This will net %d fleet value per construction tick by round end with %s and %d roids" % (
            best_income[0],
            government.title(),
            p.size,
        )
        reply += " (%s: %d | %s: %d using %s guards)" % (
            best[1],
            best_income[1],
            best[2],
            best_income[2],
            best_guards[1],
        )
        reply += " (P: %s, age: %s | D: %s, age: %s)" % (
            planet_id,
            tick - planet_tick,
            dev_id,
            tick - dev_tick,
        )
        irc_msg.reply(reply)
        return
