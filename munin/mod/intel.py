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

# Nothing alliance specific in here as far as I can tell.
# qebab, 24/6/08.

import re
from munin import loadable


class intel(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 50)
        self.paramre = re.compile(r"^\s*(.*)")
        self.commentre = re.compile(r"comment=", flags=re.IGNORECASE)
        self.usage = self.__class__.__name__ + " <x:y:z> [option=value]+"
        self.planet_coordre = re.compile(r"(\d+)[. :-](\d+)[. :-](\d+)(.*)")
        self.gal_coordre = re.compile(r"(\d+)[. :-](\d+)")
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
        self.helptext = ["Valid options: %s" % (", ".join(self.options))]

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 1

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 1

        par = m.group(1)
        m = self.planet_coordre.search(par)
        if not m:
            m = self.gal_coordre.search(par)
            if m:
                return self.exec_gal(irc_msg, m.group(1), m.group(2))
            else:
                irc_msg.reply("Usage: %s" % (self.usage,))
                return 1

        p = loadable.planet(x=m.group(1), y=m.group(2), z=m.group(3))

        params = m.group(4)

        if not p.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply("No planet matching '%s:%s:%s' found" % (p.x, p.y, p.z,))
            return 1

        i = loadable.intel(pid=p.id)
        if not i.load_from_db(self.cursor, irc_msg.round):
            pass

        opts = self.split_opts(params)
        opts["pid"] = p.id
        a = loadable.alliance(name=i.alliance)
        if i.alliance:
            a.load_most_recent(self.cursor, irc_msg.round)
        for opt, val in list(opts.items()):
            if opt == "alliance":
                if val in self.nulls:
                    a = loadable.alliance(id=None)
                    continue
                a = loadable.alliance(name=val)
                if not a.load_most_recent(self.cursor, irc_msg.round):
                    irc_msg.reply(
                        "'%s' is not a valid alliance, your information was not added."
                        % (val,)
                    )
                    return 1
                else:
                    opts["alliance"] = a.name
            if (opt in self.options) and (val in self.nulls):
                opts[opt] = None
                continue
            if opt in ("nick", "fakenick", "bg", "gov", "reportchan"):
                opts[opt] = val
            if opt in ("defwhore", "covop", "scanner", "distwhore", "relay"):
                if val in self.true:
                    opts[opt] = True
                if val in self.false:
                    opts[opt] = False
            if opt == "comment":
                opts[opt] = self.commentre.split(irc_msg.command)[1]

        for k in self.options:
            if k not in opts:
                opts[k] = getattr(i, k)

        if i.id:
            query = "UPDATE intel SET "
            query += "pid=%s,nick=%s,fakenick=%s,defwhore=%s,gov=%s,bg=%s,covop=%s,alliance_id=%s,relay=%s,reportchan=%s,"
            query += "scanner=%s,distwhore=%s,comment=%s"
            query += " WHERE id=%s"
            self.cursor.execute(
                query,
                (
                    opts["pid"],
                    opts["nick"],
                    opts["fakenick"],
                    opts["defwhore"],
                    opts["gov"],
                    opts["bg"],
                    opts["covop"],
                    a.id,
                    opts["relay"],
                    opts["reportchan"],
                    opts["scanner"],
                    opts["distwhore"],
                    opts["comment"],
                    i.id,
                ),
            )
        elif params:
            query = "INSERT INTO intel (round,pid,nick,fakenick,defwhore,gov,bg,covop,relay,reportchan,scanner,distwhore,comment,alliance_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            self.cursor.execute(
                query,
                (
                    irc_msg.round,
                    opts["pid"],
                    opts["nick"],
                    opts["fakenick"],
                    opts["defwhore"],
                    opts["gov"],
                    opts["bg"],
                    opts["covop"],
                    opts["relay"],
                    opts["reportchan"],
                    opts["scanner"],
                    opts["distwhore"],
                    opts["comment"],
                    a.id,
                ),
            )
        i = loadable.intel(
            pid=opts["pid"],
            nick=opts["nick"],
            fakenick=opts["fakenick"],
            defwhore=opts["defwhore"],
            gov=opts["gov"],
            bg=opts["bg"],
            covop=opts["covop"],
            alliance=opts["alliance"],
            relay=opts["relay"],
            reportchan=opts["reportchan"],
            scanner=opts["scanner"],
            distwhore=opts["distwhore"],
            comment=opts["comment"],
        )

        reply = "Information stored for %s:%s:%s - " % (p.x, p.y, p.z)
        reply += i.__str__()
        irc_msg.reply(reply)

        return 1

    def split_opts(self, params):
        param_dict = {}
        for s in params.split():
            a = s.split("=")
            if len(a) != 2:
                continue
            param_dict[a[0].lower()] = a[1]
        return param_dict

    def exec_gal(self, irc_msg, x, y):
        query = "SELECT i.id AS id, p.id AS pid, p.x AS x, p.y AS y, p.z AS z, i.nick AS nick, i.fakenick AS fakenick, i.defwhore AS defwhore, i.gov AS gov, i.bg AS bg, i.covop AS covop, i.alliance_id AS alliance_id, i.relay AS relay, i.reportchan AS reportchan, i.scanner AS scanner, i.distwhore AS distwhore, i.comment AS comment, a.name AS alliance"
        query += " FROM planet_dump AS p, intel AS i"
        query += " LEFT JOIN alliance_canon AS a ON i.alliance_id=a.id"
        query += " WHERE tick=(SELECT max_tick(%s::smallint)) AND p.round=%s AND p.id=i.pid AND x=%s AND y=%s"
        query += " ORDER BY z ASC"
        self.cursor.execute(query, (irc_msg.round, irc_msg.round, x, y,))

        replied_to_request = False

        repls = []
        for d in self.cursor.fetchall():
            x = d["x"]
            y = d["y"]
            z = d["z"]
            i = loadable.intel(
                pid=d["pid"],
                nick=d["nick"],
                fakenick=d["fakenick"],
                defwhore=d["defwhore"],
                gov=d["gov"],
                bg=d["bg"],
                covop=d["covop"],
                alliance=d["alliance"],
                relay=d["relay"],
                reportchan=d["reportchan"],
                scanner=d["scanner"],
                distwhore=d["distwhore"],
                comment=d["comment"],
            )
            if i.nick or i.alliance:
                replied_to_request = True
                r = "#%d " % (z,)
                if i.nick and i.alliance:
                    r += "%s [%s]" % (i.nick, i.alliance[:3])
                elif i.nick:
                    r += i.nick
                elif i.alliance:
                    r += "[" + i.alliance[:3] + "]"
                repls.append(r)

        if not replied_to_request:
            irc_msg.reply("No information stored for galaxy %s:%s" % (x, y))
        else:
            reply = "Intel %d:%d - " % (x, y)
            reply += self.gal_info(x, y, irc_msg.round)
            reply += " - "
            reply += " - ".join(repls)
            irc_msg.reply(reply)
        return 1

    def gal_info(self, x, y, round):
        g = loadable.galaxy(x=x, y=y)
        g.load_most_recent(self.cursor, round)
        return "Score (%d) Value (%d) Size (%d)" % (
            g.score_rank,
            g.value_rank,
            g.size_rank,
        )
