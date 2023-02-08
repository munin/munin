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
        self.paramre = re.compile(r"^\s*(?:(\d+)[.-:\s](\d+)[.-:\s](\d+))?(.*)")
        self.govre = re.compile(r"\s*(cor|dem|nat|soc|tot|ana)?")
        self.usage = self.__class__.__name__ + " [x:y:z] [government]"
        self.helptext = [
            "Get advice about whether to build refineries, FCs, or SCs. If no government is given, Totalitarianism is assumed."
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

        m = self.paramre.search(irc_msg.command_parameters)
        if m:
            if m.group(1):
                p = loadable.planet(x=m.group(1),
                                    y=m.group(2),
                                    z=m.group(3))
                if not p.load_most_recent(self.cursor, irc_msg.round):
                    irc_msg.reply("No planet matching '%s' found" % (param,))
                    return 1
            else:
                u = loadable.user(pnick=irc_msg.user)
                if u.load_from_db(self.cursor, irc_msg.round) and u.planet:
                    p = u.planet
                else:
                    irc_msg.reply(
                        "You must be registered to use the automatic "
                        + self.__class__.__name__
                        + " command (log in with Q and set mode +x, then make sure you've set your planet with the pref command)"
                    )
                    return 1
            m = self.govre.search(m.group(4))
            gov = m.group(1)
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
        government = governments[gov] if gov else "totalitarianism"

        self.cursor.execute("SELECT max_tick(%s::smallint)", (
            irc_msg.round,
        ))
        tick = self.cursor.fetchone()["max_tick"]

        guards      = None
        roids       = None
        planet_tick = None
        planet_id   = None
        query = """
        SELECT p.guards, p.roid_metal + p.roid_crystal + p.roid_eonium AS roids, s.tick, s.rand_id
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
            roids       = row["roids"]
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
            if not scs:
                irc_msg.reply("I need a recent planet and development scan")
                return 1
            else:
                irc_msg.reply("I need a recent planet scan")
                return 1
        elif not scs:
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
        cons_value = 200
        # print("Race CU: %s | Gov CU speed: %s | Net CU/tick: %s | Ref time %.1f | FC time %.1f | SC time %.1f" % (
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
        unbuffed_income = 250 * roids + 60000 + 1100 * (mrefs + crefs + erefs)

        gov_alert_bonus = float(self.config.get("Planetarion", "%s_alert_bonus" % (government,)))
        alert = int((50 + 5 * guards / (roids + 1)) * (1.4 + 0.0275 * scs + gov_alert_bonus))
        def guards_needed(alert,
                          scs,
                          gov_construction_speed,
                          roids):
            return max(
                0,
                math.ceil((alert / (1.4 + 0.0275 * scs + gov_alert_bonus) - 50) / 5 * (roids + 1))
            )

        guards_needed_with_current_scs = guards_needed(alert,
                                                       scs,
                                                       gov_alert_bonus,
                                                       roids)
        guards_needed_with_one_more_sc = guards_needed(alert,
                                                       scs + 1,
                                                       gov_alert_bonus,
                                                       roids)
        fireable_guards = int(guards_needed_with_current_scs - guards_needed_with_one_more_sc)

        ref_income = round(((1100 * (1 + bonus)      * (ticks_left - ref_build_time) - ref_cost) / gov_value_conversion) * cons_speed / ref_cu)
        fc_income =  round(((unbuffed_income * 0.005 * (ticks_left -  fc_build_time) -  fc_cost) / gov_value_conversion) * cons_speed /  fc_cu)
        sc_income =  round(((fireable_guards * 12    * (ticks_left -  sc_build_time) -  sc_cost) / gov_value_conversion) * cons_speed /  sc_cu)

        # print("Refs: %s/%s/%s | Min refs: %s | Ref cost: %s | Ticks left: %s | Bonus %s | Ref build time: %s | Gov value conversion: %s | Net ref income: %s" % (
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
        # print("FCs: %s | FC cost: %s | Ticks left: %s | FC build time: %s | Unbuffed income: %s | Gov value conversion: %s | Net FC income: %s" % (
        #     fcs,
        #     fc_cost,
        #     ticks_left,
        #     fc_build_time,
        #     unbuffed_income,
        #     gov_value_conversion,
        #     fc_income,
        # ))
        # print("SCs: %s | SC cost: %s | Ticks left: %s | SC build time: %s | Alert: %s | Guards now: %s | Guards after extra SC: %s | Fireable guards: %s | Net SC income: %s" % (
        #     scs,
        #     sc_cost,
        #     ticks_left,
        #     sc_build_time,
        #     alert,
        #     guards_needed_with_current_scs,
        #     guards_needed_with_one_more_sc,
        #     fireable_guards,
        #     sc_income,
        # ))

        print("%s %s %s" % (sc_income, ref_income, fc_income,))
        reply = "Planet %s:%s:%s should build a" % (
            p.x,
            p.y,
            p.z,
        )
        if sc_income > max(ref_income, fc_income):
            reply += "n SC! This will net %d fleet value per construction tick by round end with %s (Ref: %d, FC: %s" % (
                sc_income,
                government.title(),
                ref_income,
                fc_income,
            )
        elif ref_income > fc_income:
            reply += " refinery! This will net %d fleet value per construction tick by round end with %s (FC: %d, SC: %s" % (
                ref_income,
                government.title(),
                fc_income,
                sc_income,
            )
        else:
            reply += "n FC! This will net %d fleet value per construction tick by round end with %s (Ref: %d, SC: %s" % (
                fc_income,
                government.title(),
                ref_income,
                sc_income,
            )
        reply += ") (P: %s, pt: %s | D: %s, pt: %s)" % (
            planet_id,
            planet_tick,
            dev_id,
            dev_tick,
        )
        irc_msg.reply(reply)
        return
