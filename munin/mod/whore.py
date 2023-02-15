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

# Nothing hardcoded found here.
# qebab, 24/6/08.

import re
from munin import loadable


class whore(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(.*)")
        self.alliancere = re.compile(r"^(\S+)$")
        self.racere = re.compile(r"^(ter|cat|xan|zik|eit|etd|kin|sly)$", re.I)
        self.rangere = re.compile(r"^(<|>)?(\d+[kmbKMB]?)$")
        self.clusterre = re.compile(r"^c(\d+)$", re.I)
        self.usage = (
            self.__class__.__name__
            + " [alliance] [race] [<|>][size] [<|>][value] [c<cluster>] [bash]"
            + " (must include at least one search criteria, order doesn't matter)"
        )
        self.helptext = [
            "Show planets you can gain the most XP from"
        ]

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        if not user:
            irc_msg.reply(
                "You must be registered to use the "
                + self.__class__.__name__
                + " command (log in with Q and set mode +x)"
            )
            return 1

        attacker = None
        u = loadable.user(pnick=irc_msg.user)
        if not u.load_from_db(self.cursor, irc_msg.round):
            irc_msg.reply(
                "Usage: %s (you must set your planet in preferences to use this command (!pref planet=x:y:z))"
                % (self.usage,)
            )
            return 1
        if u.planet_id and u.planet_id > 0:
            attacker = u.planet
        else:
            irc_msg.reply(
                "Usage: %s (you must set your planet in preferences to use this command (!pref planet=x:y:z))"
                % (self.usage,)
            )
            return 1

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        alliance = None
        race = None
        size_mod = None
        size = None
        value_mod = None
        value = None
        cluster = None
        param = m.group(1)
        params = param.split()

        for p in params:
            m = self.clusterre.search(p)
            if m and not cluster:
                cluster = int(m.group(1))
                continue
            m = self.racere.search(p)
            if m and not race:
                race = m.group(1)
                continue
            m = self.rangere.search(p)
            if m and not size:
                numeric = self.human_readable_number_to_integer(m.group(2))
                if numeric < 32768:
                    size_mod = m.group(1) or ">"
                    size = m.group(2)
                    continue
            m = self.rangere.search(p)
            if m and not value:
                value_mod = m.group(1) or "<"
                value = self.human_readable_number_to_integer(m.group(2))
                continue
            m = self.alliancere.search(p)
            if m and not alliance and not self.clusterre.search(p):
                alliance = m.group(1)
                continue

        victims = self.victim(
            irc_msg.round,
            alliance,
            race,
            size_mod,
            size,
            value_mod,
            value,
            attacker,
            True,
            cluster,
        )
        i = 0
        if not len(victims):
            reply = "No"
            if race:
                reply += " %s" % (race,)
            reply += " planets"
            if alliance:
                reply += " in intel matching alliance: %s" % (alliance,)
            else:
                reply += " matching"
            if size:
                reply += " Size %s %s" % (size_mod, size)
            if value:
                reply += " Value %s %s" % (value_mod, value)
            if cluster:
                reply += " Cluster %s" %(cluster,)
            irc_msg.reply(reply)
        for v in victims:
            reply = "%s:%s:%s (%s)" % (v["x"], v["y"], v["z"], v["race"])
            reply += " Value: %s Size: %s Scoregain: %d+" % (
                v["value"],
                v["size"],
                v["xp_gain"] * 60,
            )
            if v["nick"]:
                reply += " Nick: %s" % (v["nick"],)
            if not alliance and v["alliance"]:
                reply += " Alliance: %s" % (v["alliance"],)
            i += 1
            if i > 4 and len(victims) > 4:
                reply += " (Too many victims to list, please refine your search)"
                irc_msg.reply(reply)
                break
            irc_msg.reply(reply)

        return 1

    def victim(
        self,
        round,
        alliance=None,
        race=None,
        size_mod=">",
        size=None,
        value_mod="<",
        value=None,
        attacker=None,
        bash=True,
        cluster=None,
    ):
        args = (
            attacker.score,
            attacker.xp,
            attacker.xp,
            attacker.score,
            attacker.value,
            attacker.value,
            round,
            round,
        )

        # Behold! The worst SQL query.
        query = """
        SELECT float8smaller(%s / 180.0,
                             raw_xp * (0.95 ^ ((%s + (raw_xp * 1.5)) / 10000.0)) * float8smaller(1.25,
                                                                                                 -float8smaller(-0.1,
                                                                                                                -(1.5 - %s / 200000.0))))::int AS xp_gain,
               x, y, z, size, value, race, alliance, nick
        FROM (
              SELECT cap * 5 * bravery AS raw_xp,
                     *
              FROM (
                    SELECT float8smaller(2.0,
                                         -float8smaller(-0.2,
                                                        -float8smaller(2.25,
                                                                       score / %s::float) - 0.25) * -float8smaller(-0.2,
                                                                                                                   -float8smaller(2.25,
                                                                                                                                  value / %s::float) - 0.25)) AS bravery,
                           *
                    FROM (
                          SELECT (float8smaller(0.25,
                                                0.25 * sqrt(p.value / %s::float)) * p.size)::int AS cap,
                                  p.x, p.y, p.z, p.size, p.value, p.score, p.race,
                                  a.name AS alliance,
                                  i.nick
                         FROM      planet_dump    AS p
                         LEFT JOIN intel          AS i ON p.id=i.pid
                         LEFT JOIN alliance_canon AS a ON i.alliance_id=a.id
                         WHERE p.tick=(SELECT max_tick(%s::smallint))
                         AND p.round=%s
                    ) AS with_cap
              ) AS with_bravery
        ) AS with_raw_xp
        WHERE 1 = 1
        """

        if alliance:
            query += " AND alliance ILIKE %s"
            args += ("%%%s%%" % (alliance,),)
        if race:
            query += " AND race ILIKE %s"
            args += (race,)
        if size:
            query += " AND size %s %%s" % (size_mod,)
            args += (size,)
        if value:
            query += " AND value %s %%s" % (value_mod,)
            args += (value,)
        if bash:
            query += " AND (value > %s OR score > %s)"
            args += (attacker.value * 0.5, attacker.score * 0.6)
        if cluster:
            query += " AND x = %s::smallint"
            args += (cluster,)
        query += " ORDER BY xp_gain DESC, size DESC, value DESC LIMIT 6"

        self.cursor.execute(query, args)
        return self.cursor.fetchall()
