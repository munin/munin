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

# Nothing alliance specific in this module as far as I can tell.
# qebab, 24/6/08.

import re
from munin import loadable


class search(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 50)
        self.paramre = re.compile(r"^\s*(.*)")
        self.paramsplitre = re.compile(r"\s+")
        self.usage = self.__class__.__name__ + " <alliance|nick|option=value>+"
        self.options = [
            "alliance",
            "nick",
            "fakenick",
            "defwhore",
            "covop",
            "scanner",
            "distwhore",
            "bg",
            "gov",
            "relay",
            "reportchan",
            "comment",
        ]
        self.nulls = ["<>", ".", "-", "?", ""]
        self.true = ["1", "yes", "y", "true", "t"]
        self.false = ["0", "no", "n", "false", "f", ""]
        self.helptext = [
            "Valid options: %s" % (", ".join(self.options))
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        options = self.split_opts(m.group(1))

        query = (
            "SELECT p.x, p.y, p.z, p.size, p.score, p.value, p.race,"
            "       a.name AS alliance,"
            "       i.nick, i.fakenick, i.defwhore, i.covop, i.scanner, i.distwhore, i.bg, i.gov, i.relay, i.reportchan, i.comment"
            " FROM planet_dump          AS p"
            " INNER JOIN planet_canon   AS c ON p.id=c.id"
            " INNER JOIN intel          AS i ON c.id=i.pid"
            " LEFT  JOIN alliance_canon AS a ON i.alliance_id=a.id"
            " WHERE p.tick=(SELECT max_tick(%s::smallint))"
            " AND p.round=%s"
        )
        args = (irc_msg.round, irc_msg.round,)
        for key, value in options.items():
            if key == 'nick_or_alliance':
                query += " AND (a.name ILIKE %s OR i.nick ILIKE %s)"
                args += ("%" + value + "%", "%" + value + "%",)
            elif key == 'alliance':
                query += " AND a.name ILIKE %s"
                args += ("%%%s%%" % (value,),)
            elif type(value) == str:
                # No SQL vuln here: split_opts() ensures that the column name
                # is one of the purely alphabetic strings in self.options, so
                # we can safely paste it in.
                query += " AND i.%s ILIKE %%s" % (key,)
                args += ("%%%s%%" % (value,),)
            else:
                query += " AND i.%s = %%s" % (key,)
                args += (value,)
        query += " LIMIT 6"
        self.cursor.execute(query, args)

        i = 0
        planets = self.cursor.fetchall()
        if not len(planets):
            reply = "No planets in intel matching search query"
            irc_msg.reply(reply)
            return 1
        for p in planets:
            intels = [
                "%s: %s" % (key.title(), p[key],)
                for key in self.options
                if key in p and p[key]
            ]
            reply = "%s:%s:%s (%s) Score: %s Value: %s Size: %s %s" % (
                p["x"],
                p["y"],
                p["z"],
                p["race"],
                p["score"],
                p["value"],
                p["size"],
                ' '.join(intels),
            )
            i += 1
            if i > 4 and len(planets) > 4:
                reply += " (Too many results to list, please refine your search)"
                irc_msg.reply(reply)
                break
            irc_msg.reply(reply)

        return 1

    def split_opts(self, params):
        param_dict = {}
        for s in re.split(self.paramsplitre, params):
            if '=' in s:
                key, value = s.split('=')
                if key in self.options:
                    if key == 'nick':
                        value = value.removeprefix('@')
                    if value in self.nulls:
                        value = None
                    if value in self.true:
                        value = True
                    if value in self.false:
                        value = False
                    param_dict[key] = value
                # Silently ignore invalid options
            else:
                # For simplicity, allow plain alliance and nick.
                param_dict['nick_or_alliance'] = s.removeprefix('@')
        return param_dict
