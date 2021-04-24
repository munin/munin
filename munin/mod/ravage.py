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


class ravage(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(.*)")
        self.alliancere = re.compile(r"^(\S+)$")
        self.racere = re.compile(r"^(ter|cat|xan|zik|eit|etd)$", re.I)
        self.rangere = re.compile(r"^(<|>)?(\d+)$")
        self.bashre = re.compile(r"^(bash)$", re.I)
        self.clusterre = re.compile(r"^c(\d+)$", re.I)
        self.usage = (
            self.__class__.__name__
            + " [alliance] [race] [<|>][vulnerable structures] [<|>][size] [<|>][value] [c<cluster>] [bash]"
            + " (must include at least one search criteria, order doesn't matter)"
        )
        self.helptext = [
            "Show planets you can kill the most structures on. Only planets for which a development scan is available are included."
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        alliance = None
        race = None
        structure_mod = None
        structures = None
        size_mod = None
        size = None
        value_mod = None
        value = None
        bash = False
        attacker = None
        cluster = None

        param = m.group(1)
        params = param.split()

        for p in params:
            m = self.bashre.search(p)
            if m and not bash:
                bash = True
                continue
            m = self.clusterre.search(p)
            if m and not cluster:
                cluster = int(m.group(1))
            m = self.racere.search(p)
            if m and not race:
                race = m.group(1)
                continue
            m = self.rangere.search(p)
            # Max structures is 400, at most 10% of which can be SKed. Larger
            # numbers are probably meant to be roids or value.
            if m and not structures and int(m.group(2)) <= 40:
                structure_mod = m.group(1) or ">"
                structures = m.group(2)
                continue
            if m and not size and int(m.group(2)) < 32768:
                size_mod = m.group(1) or ">"
                size = m.group(2)
                continue
            m = self.rangere.search(p)
            if m and not value:
                value_mod = m.group(1) or "<"
                value = m.group(2)
                continue
            m = self.alliancere.search(p)
            if m and not alliance and not self.clusterre.search(p):
                alliance = m.group(1)
                continue

        if bash:
            if not user:
                irc_msg.reply(
                    "You must be registered to use the %s command's bash option (log in with P and set mode +x)"
                    % (self.__class__.__name__,)
                )
                return 1
            u = loadable.user(pnick=irc_msg.user)
            if not u.load_from_db(self.cursor, irc_msg.round):
                irc_msg.reply(
                    "Usage: %s (you must set your planet in preferences to use the bash option (!pref planet=x:y:z))"
                    % (self.usage,)
                )
                return 1
            if u.planet_id and u.planet_id > 0:
                attacker = u.planet
            else:
                irc_msg.reply(
                    "Usage: %s (you must set your planet in preferences to use the bash option (!pref planet=x:y:z))"
                    % (self.usage,)
                )
                return 1

        victims = self.ravage(
            irc_msg.round,
            alliance,
            race,
            structure_mod,
            structures,
            size_mod,
            size,
            value_mod,
            value,
            attacker,
            bash,
            cluster
        )

        if not len(victims):
            reply = "No"
            if race:
                reply += " %s" % (race,)
            reply += " planets"
            if alliance:
                reply += " in intel matching Alliance: %s" % (alliance,)
            else:
                reply += " matching"
            if size:
                reply += " Size %s %s" % (size_mod, size)
            if value:
                reply += " Value %s %s" % (value_mod, value)
            if structures:
                reply += " Vulnerable structures %s %s" % (structure_mod, structures)
            irc_msg.reply(reply)
        i = 0
        for v in victims:
            if i < 5:
                reply = "%s:%s:%s (%s)" % (v["x"], v["y"], v["z"], v["race"])
                reply += " Value: %s Size: %s Vulnerable: %s" % (v["value"], v["size"], v["vulnerable"])
                if v["nick"]:
                    reply += " Nick: %s" % (v["nick"],)
                if not alliance and v["alliance"]:
                    reply += " Alliance: %s" % (v["alliance"],)
                i += 1
                if i > 4 and len(victims) > 5:
                    reply += " (Too many ravage targets to list, please refine your search)"
                irc_msg.reply(reply)
        return 1

    def ravage(
            self,
            round,
            alliance=None,
            race=None,
            structure_mod='>',
            structures=None,
            size_mod=">",
            size=None,
            value_mod="<",
            value=None,
            attacker=None,
            bash=None,
            cluster=None
    ):
        args = (
            round,
            round,
        )
        query = (
            "SELECT *"
            " FROM ("
            "     SELECT pd.x, pd.y, pd.z, pd.size, pd.value, pd.race,"
            "            ac.name AS alliance,"
            "            i.nick,"
            "            (light_factory + medium_factory + heavy_factory + wave_amplifier + wave_distorter + metal_refinery + crystal_refinery + eonium_refinery + research_lab + finance_centre + military_centre + security_centre + structure_defense) - (10 * structure_defense) AS vulnerable,"
            "            rank() OVER (PARTITION BY s.pid ORDER BY s.id DESC) AS rank"
            "     FROM       planet_dump    AS pd"
            "     INNER JOIN planet_canon   AS pc ON pc.id     = pd.id"
            "     INNER JOIN scan           AS s  ON s.pid     = pc.id"
            "     INNER JOIN development    AS d  ON d.scan_id = s.id"
            "     LEFT JOIN  intel          AS i  ON i.pid     = pd.id"
            "     LEFT JOIN  alliance_canon AS ac ON ac.id     = i.alliance_id"
            "     WHERE pd.tick = (SELECT max_tick(%s::smallint))"
            "     AND pd.round = %s"
        )

        if alliance:
            query += "     AND ac.name ILIKE %s"
            args += ("%" + alliance + "%",)
        if race:
            query += "     AND race ILIKE %s"
            args += (race,)
        if size:
            query += "     AND size %s %%s" % (size_mod,)
            args += (size,)
        if value:
            query += "     AND value %s %%s" % (value_mod,)
            args += (value,)
        if bash:
            query += "     AND (value > %s OR score > %s)"
            args += (attacker.value * 0.4, attacker.score * 0.6,)
        if cluster:
            query += "     AND x = %s::smallint"
            args += (cluster,)

        query += (
            "     ORDER BY pd.size DESC, pd.value DESC"
            " ) AS results"
            " WHERE rank = 1"
            " AND vulnerable > 0"
        )
        if structures:
            query += " AND vulnerable %s %%s" % (structure_mod,)
            args += (structures,)
        query += " LIMIT 6"
        self.cursor.execute(query, args)
        return self.cursor.fetchall()
