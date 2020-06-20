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

# No alliance specific things in this module as far as I can tell.
# qebab, 24/6/08.

import re
from munin import loadable


class idler(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 50)
        self.paramre = re.compile(r"^\s*(.*)")
        self.alliancere = re.compile(r"^(\S+)$")
        self.racere = re.compile(r"^(ter|cat|xan|zik|eit|etd)$", re.I)
        self.rangere = re.compile(r"^(<|>)?(\d+)$")
        self.bashre = re.compile(r"^(bash)$", re.I)
        self.clusterre = re.compile(r"^c(\d+)$", re.I)
        self.usage = (
            self.__class__.__name__
            + " [alliance] [race] [<|>][size] [<|>][value] [bash]"
            + " (must include at least one search criteria, order doesn't matter)"
        )

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0


        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        alliance = None
        race = None
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
                    "You must be registered to use the "
                    + self.__class__.__name__
                    + " command's bash option (log in with P and set mode +x)"
                )
                return 1

            u = loadable.user(pnick=irc_msg.user)
            if not u.load_from_db(self.cursor, irc_msg.round):
                irc_msg.reply(
                    "Usage: %s (you must set your planet in preferences to use the bash option (!pref planet=x:y:z))"
                    % (self.usage,)
                )
                return 1
            if u.planet_id:
                attacker = u.planet
            else:
                irc_msg.reply(
                    "Usage: %s (you must set your planet in preferences to use the bash option (!pref planet=x:y:z))"
                    % (self.usage,)
                )
                return 1

        victims = self.victim(
            irc_msg.round,
            alliance,
            race,
            size_mod,
            size,
            value_mod,
            value,
            attacker,
            bash,
            cluster,
        )
        i = 0
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
            irc_msg.reply(reply)
        for v in victims:
            reply = "%s:%s:%s (%s)" % (v["x"], v["y"], v["z"], v["race"])
            reply += " Value: %s Size: %s Idle: %s" % (v["value"], v["size"], v["idle"])
            if v["nick"]:
                reply += " Nick: %s" % (v["nick"],)
            if not alliance and v["alliance"]:
                reply += " Alliance: %s" % (v["alliance"],)
            i += 1
            if i > 4 and len(victims) > 4:
                reply += " (Too many idlers to list, please refine your search)"
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
        bash=False,
        cluster=None,
    ):
        query = "SELECT p.x AS x,p.y AS y,p.z AS z,p.size AS size,p.size_rank AS size_rank,p.value AS value,p.value_rank AS value_rank,p.race AS race,p.idle AS idle,a.name AS alliance,i.nick AS nick"
        query += " FROM       planet_dump    AS p"
        query += " INNER JOIN planet_canon   AS c ON p.id=c.id"
        query += " LEFT JOIN  intel          AS i ON p.id=i.pid"
        query += " LEFT JOIN  alliance_canon AS a ON a.id=i.alliance_id"
        query += " WHERE p.x<200 AND p.tick=(SELECT max_tick(%s::smallint)) AND p.round=%s AND p.vdiff<>0"
        args = (
            round,
            round,
        )

        if alliance:
            query += " AND a.name ILIKE %s"
            args += ("%" + alliance + "%",)
        if race:
            query += " AND race ILIKE %s"
            args += (race,)
        if size:
            query += " AND size %s " % (size_mod) + "%s"
            args += (size,)
        if value:
            query += " AND value %s " % (value_mod) + "%s"
            args += (value,)
        if bash:
            query += " AND (value > %s OR score > %s)"
            args += (attacker.value * 0.4, attacker.score * 0.6)
        if cluster:
            query += " AND x = %s::smallint"
            args += (cluster,)

        query += " ORDER BY p.idle DESC, p.value DESC"
        self.cursor.execute(query, args)
        return self.cursor.fetchall()
