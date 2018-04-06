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

import re
from munin import loadable


class anarchy(loadable.loadable):
    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(.*)")
        self.usage = self.__class__.__name__ + " [x:y:z]"
        self.helptext = ['Lists all planets currently in anarchy or anarchy information about a specific planet']

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.match(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        params = m.group(1)
        m = self.planet_coordre.search(params)

        current_tick = self.current_tick(irc_msg.round)

        if m:
            x = m.group(1)
            y = m.group(2)
            z = m.group(3)

            planet = loadable.planet(x=x, y=y, z=z)
            if not planet.load_most_recent(self.cursor, irc_msg.round):
                irc_msg.reply("No planet matching %s:%s:%s found" % (x, y, z))
                return 0

            reply = "%s:%s:%s" % (x, y, z)

            query = "SELECT a.start_tick, a.end_tick"
            query += " FROM anarchy AS a"
            query += " INNER JOIN planet_dump AS p ON a.pid = p.id"
            query += " WHERE p.round = %s"
            query += " AND p.tick = %s"
            query += " AND p.x = %s"
            query += " AND p.y = %s"
            query += " AND p.z = %s"
            query += " ORDER BY a.end_tick ASC"
            self.cursor.execute(query, (irc_msg.round, current_tick, x, y, z))
            current_end_tick = None
            anarchy_list = []
            for period in self.cursor.dictfetchall():
                end = period['end_tick']
                if end > current_tick:
                    current_end_tick = end
                else:
                    anarchy_list.append("%d-%d" % (period['start_tick'], period['end_tick']))
            if len(anarchy_list) == 0:
                reply += " has had no previous periods of anarchy"
            else:
                reply += " was previously in anarchy between ticks: %s" % (", ".join(anarchy_list))

            if current_end_tick:
                reply += " and is currently in anarchy until tick %d" % (current_end_tick)
                needed_scans = []

                # Get guards from planet scan.
                query = "SELECT scan.tick, guards"
                query += " FROM scan INNER JOIN planet ON scan.id = planet.scan_id"
                query += " WHERE scan.pid = %s "
                query += " ORDER BY scan.scan_time DESC"
                query += " LIMIT 1"
                self.cursor.execute(query, (planet.id,))
                if self.cursor.rowcount < 1:
                    needed_scans.append('planet')
                else:
                    planet_scan = self.cursor.dictfetchone()
                    guards = planet_scan['guards']
                    planet_tick = planet_scan['tick']

                # Get SCs and total number of constructions from development
                # scan.
                query = "SELECT scan.tick, light_factory, medium_factory, heavy_factory, wave_amplifier, wave_distorter, metal_refinery,"
                query += " crystal_refinery, eonium_refinery, research_lab, finance_centre, military_centre, security_centre, structure_defense"
                query += " FROM scan INNER JOIN development ON scan.id = development.scan_id"
                query += " WHERE scan.pid = %s"
                query += " ORDER BY scan.scan_time DESC"
                query += " LIMIT 1"
                self.cursor.execute(query, (planet.id,))
                if self.cursor.rowcount < 1:
                    needed_scans.append('development')

                if len(needed_scans) == 0:
                    dev_scan = self.cursor.dictfetchone()
                    sc = dev_scan['security_centre']
                    total = (dev_scan['light_factory'] + dev_scan['medium_factory'] + dev_scan['heavy_factory'] +
                             dev_scan['wave_amplifier'] + dev_scan['wave_distorter'] +
                             dev_scan['metal_refinery'] + dev_scan['crystal_refinery'] + dev_scan['eonium_refinery'] +
                             dev_scan['research_lab'] + dev_scan['structure_defense'] +
                             dev_scan['finance_centre'] + dev_scan['military_centre'] + dev_scan['security_centre']
                             )
                    development_tick = dev_scan['tick']

                    min_alert = (1 - 0.15       + float(sc) / total) * (50 + 5 * float(guards) / float(planet.size + 1))
                    max_alert = (1 - 0.15 + 0.5 + float(sc) / total) * (50 + 5 * float(guards) / float(planet.size + 1))
                    reply += ", with a minimum alert of %d and a maximum of %d (planet scan from pt%d, dev scan from pt%d)" % (
                        int(min_alert), int(max_alert), planet_tick, development_tick)
                else:
                    reply += ", need a %s scan to calculate alert" % (" and ".join(needed_scans))
            else:
                reply += " and is not currently in anarchy"
        else:
            query = "SELECT p.x, p.y, p.z"
            query += " FROM anarchy AS a"
            query += " INNER JOIN planet_dump AS p ON a.pid = p.id"
            query += " WHERE p.round = %s"
            query += " AND a.start_tick < %s"
            query += " AND a.end_tick > %s"
            query += " AND p.tick = %s"
            query += " ORDER BY p.x ASC, p.y ASC, p.z ASC"
            query += " LIMIT 120"
            self.cursor.execute(query, (irc_msg.round, current_tick, current_tick, current_tick))
            if self.cursor.rowcount < 1:
                reply = "There are currently no planets in anarchy. Get to it!"
            else:
                anarchy_list = ["%d:%d:%d" % (p['x'], p['y'], p['z']) for p in self.cursor.dictfetchall()]
                reply = "Planets currently in anarchy: %s" % (", ".join(anarchy_list))
                if self.cursor.rowcount == 120:
                    reply += " and a bunch more"

        irc_msg.reply(reply)
        return 1
