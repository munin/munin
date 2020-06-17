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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

# Nothing ascendancy/jester specific (aside from infrajerome.)
# qebab, 24/6/08.

import re
from munin import loadable


class dev(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 50)
        self.paramre = re.compile(r"^\s*(.*)")
        self.usage = self.__class__.__name__ + " <x:y:z>"
        self.helptext = None

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        params = m.group(1)
        m = self.planet_coordre.search(params)

        reply = ""
        if m:
            x = m.group(1)
            y = m.group(2)
            z = m.group(3)

            p = loadable.planet(x=x, y=y, z=z)
            if not p.load_most_recent(self.cursor, irc_msg.round):
                irc_msg.reply("No planet matching '%s' found" % (params,))
                return 1

            query = "SELECT t2.id AS id,t1.tick,nick,scantype,rand_id,travel,infrastructure,hulls,waves,core,covert_op"
            query += ",mining,population,light_factory,medium_factory,heavy_factory,wave_amplifier,wave_distorter"
            query += ",metal_refinery,crystal_refinery,eonium_refinery,research_lab,finance_centre,military_centre"
            query += ",security_centre,structure_defense"
            query += " FROM scan AS t1 INNER JOIN development AS t2 ON t1.id=t2.scan_id"
            query += " WHERE t1.pid=%s AND t1.round=%s"
            query += " ORDER BY t1.tick DESC"
            self.cursor.execute(query, (p.id, irc_msg.round))

            if self.cursor.rowcount < 1:
                reply += "No dev scans available on %s:%s:%s" % (p.x, p.y, p.z)
            else:
                s = self.cursor.fetchone()

                total = max(1, self.get_total_cons_from_scan(self.cursor, s["id"]))

                reply += "Newest development scan on %s:%s:%s (id: %s, pt: %s)" % (
                    p.x,
                    p.y,
                    p.z,
                    s["rand_id"],
                    s["tick"],
                )
                reply += (
                    " Travel: %s, Infrajerome: %s, Hulls: %s, Waves: %s, Core: %s, Covop: %s, Mining: %s, Population: %s"
                    % (
                        s["travel"],
                        self.infra(s["infrastructure"]),
                        self.hulls(s["hulls"]),
                        self.waves(s["waves"]),
                        self.core(s["core"]),
                        self.covop(s["covert_op"]),
                        self.mining(s["mining"]),
                        self.population(s["population"]),
                    )
                )

                irc_msg.reply(reply)
                reply = (
                    "Structures: LFac: %s, MFac: %s, HFac: %s, Amp: %s, Dist: %s, MRef: %s, CRef: %s, ERef: %s, ResLab: %s (%s%%), FC: %s, Milf: %s, Sec: %s (%s%%), SD: %s (%s%%) "
                    % (
                        s["light_factory"],
                        s["medium_factory"],
                        s["heavy_factory"],
                        s["wave_amplifier"],
                        s["wave_distorter"],
                        s["metal_refinery"],
                        s["crystal_refinery"],
                        s["eonium_refinery"],
                        s["research_lab"],
                        int(float(s["research_lab"]) / total * 100),
                        s["finance_centre"],
                        s["military_centre"],
                        s["security_centre"],
                        int(float(s["security_centre"]) / total * 100),
                        s["structure_defense"],
                        int(float(s["structure_defense"]) / total * 100),
                    )
                )
                i = 0
                reply += " Older scans: "
                prev = []
                for s in self.cursor.fetchall():
                    i += 1
                    if i > 4:
                        break
                    prev.append("(%s,pt%s)" % (s["rand_id"], s["tick"]))
                reply += ", ".join(prev)

        else:
            m = self.idre.search(params)
            if not m:
                irc_msg.reply("Usage: %s" % (self.usage,))
                return 0

            rand_id = m.group(1)
            query = "SELECT t2.id AS id,x,y,z,t1.tick,nick,scantype,rand_id,travel,infrastructure,hulls,waves,core,covert_op"
            query += ",mining,light_factory,medium_factory,heavy_factory,wave_amplifier,wave_distorter"
            query += ",metal_refinery,crystal_refinery,eonium_refinery,research_lab,finance_centre,military_centre"
            query += ",security_centre,structure_defense"
            query += " FROM scan AS t1"
            query += " INNER JOIN development AS t2 ON t1.id=t2.scan_id"
            query += (
                " INNER JOIN planet_dump AS t3 ON t1.pid=t3.id AND t1.round=t3.round"
            )
            query += " WHERE t3.tick=(SELECT max_tick(%s::smallint)) AND t1.rand_id=%s AND t1.round=%s ORDER BY t1.tick DESC"
            self.cursor.execute(query, (irc_msg.round, rand_id, irc_msg.round))

            if self.cursor.rowcount < 1:
                reply += "No dev scans matching ID %s" % (rand_id,)
            else:
                s = self.cursor.fetchone()

                total = (
                    s["light_factory"]
                    + s["medium_factory"]
                    + s["heavy_factory"]
                    + s["wave_amplifier"]
                    + s["wave_distorter"]
                    + s["metal_refinery"]
                    + s["crystal_refinery"]
                    + s["eonium_refinery"]
                    + s["research_lab"]
                    + s["structure_defense"]
                    + s["finance_centre"]
                    + s["military_centre"]
                    + s["security_centre"]
                )

                reply += "Development scan on %s:%s:%s (id: %s, pt: %s)" % (
                    s["x"],
                    s["y"],
                    s["z"],
                    s["rand_id"],
                    s["tick"],
                )
                reply += (
                    " Travel: -%s, Infrajerome: %s, Hulls: %s, Waves: %s, Core: %s, Covop: %s, Mining: %s"
                    % (
                        s["travel"],
                        self.infra(s["infrastructure"]),
                        self.hulls(s["hulls"]),
                        self.waves(s["waves"]),
                        self.core(s["core"]),
                        self.covop(s["covert_op"]),
                        self.mining(s["mining"]),
                    )
                )

                irc_msg.reply(reply)
                reply = (
                    "Structures: LFac: %s, MFac: %s, HFac: %s, Amp: %s, Dist: %s, MRef: %s, CRef: %s, ERef: %s, ResLab: %s (%s%%), FC: %s, Milf: %s, Sec: %s (%s%%), SD: %s (%s%%) "
                    % (
                        s["light_factory"],
                        s["medium_factory"],
                        s["heavy_factory"],
                        s["wave_amplifier"],
                        s["wave_distorter"],
                        s["metal_refinery"],
                        s["crystal_refinery"],
                        s["eonium_refinery"],
                        s["research_lab"],
                        int(float(s["research_lab"]) / total * 100),
                        s["finance_centre"],
                        s["military_centre"],
                        s["security_centre"],
                        int(float(s["security_centre"]) / total * 100),
                        s["structure_defense"],
                        int(float(s["structure_defense"]) / total * 100),
                    )
                )

        irc_msg.reply(reply)

        return 1

    def infra(self, level):
        if level == 0:
            return "20 constructions"
        if level == 1:
            return "50 constructions"
        if level == 2:
            return "100 constructions"
        if level == 3:
            return "150 constructions"
        if level == 4:
            return "200 constructions"
        if level == 5:
            return "300 constructions"

    def hulls(self, level):
        if level == 1:
            return "FI/CO"
        if level == 2:
            return "FR/DE"
        if level == 3:
            return "CR/BS"

    def waves(self, level):
        if level == 0:
            return "Planet"
        if level == 1:
            return "Landing"
        if level == 2:
            return "Development"
        if level == 3:
            return "Unit"
        if level == 4:
            return "News"
        if level == 5:
            return "Incoming"
        if level == 6:
            return "JGP"
        if level == 7:
            return "Advanced Unit"

    def core(self, level):
        if level == 0:
            return "1000 per tick"
        if level == 1:
            return "4000 per tick"
        if level == 2:
            return "8000 per tick"
        if level == 3:
            return "15000 per tick"
        if level == 4:
            return "25000 per tick"

    def covop(self, level):
        if level == 0:
            return "Blow up roids"
        if level == 1:
            return "Steal agents"
        if level == 2:
            return "Steal guards"
        if level == 3:
            return "Steal research"
        if level == 4:
            return "Steal shits"
        if level == 5:
            return "Blow up amps & dists"
        if level == 6:
            return "DEMOLITION MAN"
        if level == 7:
            return "Resource hacking (OMG)"
        if level == 8:
            return "Anarchy in the UK!"

    def mining(self, level):
        if level == 0:
            return "100 roids (scanner!)"
        if level == 1:
            return "200 roids"
        if level == 2:
            return "300 roids"
        if level == 3:
            return "500 roids"
        if level == 4:
            return "750 roids"
        if level == 5:
            return "1000 roids"
        if level == 6:
            return "1250 roids"
        if level == 7:
            return "1500 roids"
        if level == 8:
            return "Jan 1. 1900"
        if level == 9:
            return "2500 roids"
        if level == 10:
            return "3000 roids"
        if level == 11:
            return "3500 roids"
        if level == 12:
            return "4500 roids"
        if level == 13:
            return "5500 roids"
        if level == 14:
            return "6500 roids"
        if level == 15:
            return "8000 roids"
        if level == 16:
            return "top10 or dumb"

    def population(self, level):
        if level == 0:
            return "50%"
        if level == 1:
            return "60%"
        if level == 2:
            return "70%"
        if level == 3:
            return "80%"
        if level == 4:
            return "90%"
        if level == 5:
            return "Highly efficient!"
