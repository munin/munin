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

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08

import re
import psycopg2
import urllib.request, urllib.error, urllib.parse
from munin import loadable

class putships(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1000)
        self.paramre = re.compile(r"^\s*(https?://\S+)?(\s*overwrite)?")
        self.usage = self.__class__.__name__ + " [url] [overwrite]"
        self.helptext = [
            "Load ship stats from an URL (or the default stats URL, if no URL"
            " is given. If 'overwrite' is given, remove the old stats before "
            " loading the new ones" ]

        self.mapping = {
            "Fi": "Fighter",
            "Co": "Corvette",
            "Fr": "Frigate",
            "De": "Destroyer",
            "Cr": "Cruiser",
            "Bs": "Battleship",
            "Ro": "Roids",
            "St": "Struct",
            "Ter": "Terran",
            "Etd": "Eitraides",
            "Cat": "Cathaar",
            "Zik": "Zikonian",
            "Xan": "Xandathrii",
            "Kin": "Kinthia",
            "Sly": "Slythonian",
            "Re": "Rs",  # Resources
        }
        self.keys = [
            "race",
            "name",
            "class",
            "target_1",
            "target_2",
            "target_3",
            "type",
            "is_cloaked",
            "init",
            "gun",
            "armor",
            "damage",
            "empres",
            "metal",
            "crystal",
            "eonium",
            "a/c",
            "d/c",
            "eta",
        ]
        self.skip = [
            "a/c",
            "d/c",
        ]
        regex = r'^<tr class="(Ter|Cat|Xan|Zik|Etd|Kin|Sly)">.+?>([^<]+)</td>'  # race & name
        regex += r"<td>(\w+)</td>"  # class
        regex += r"(?:<td>(\w\w|\-)</td>)?" * 3  # t1,t2,t3
        regex += r"<td>(\w+)</td>"  # type
        regex += r"<td>(Y|N)</td>"  # cloaked
        regex += r".+?(\d+|\-)</td>" * 11  # some numbers
        regex += r".*?</tr>$"  # end of the line
        self.ship_re = re.compile(regex, re.I | re.M)


    def execute(self, user, access, irc_msg):
        if access < self.level:
            irc_msg.reply("You do not have enough access to load ship stats")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        url = m.group(1) or self.config.get('Url', 'shipstats')
        overwrite = bool(m.group(2)) or False

        try:
            if self.load_stats(irc_msg.round, url, overwrite):
                self.cursor.execute("SELECT id FROM ship WHERE round=%s;", (irc_msg.round,))
                irc_msg.reply("Successfully loaded %s ships from %s into the database"
                              " for round %d" % (self.cursor.rowcount, url, irc_msg.round,))
                return 1
            else:
                irc_msg.reply("Failed to find any ships to load from URL %s" % (url,))
        except psycopg2.errors.UniqueViolation as uv:
            self.cursor.execute("SELECT id FROM ship WHERE round=%s;", (irc_msg.round,))
            irc_msg.reply("%d ships for round %d have already been loaded" % (self.cursor.rowcount, irc_msg.round,))
        return 0

    def load_stats(self, round, url, overwrite):
        if overwrite:
            self.cursor.execute("DELETE FROM ship WHERE round=%s;", (round,))

        req = urllib.request.Request(url)
        useragent = "Munin (Python-urllib/%s); BotNick/%s; Admin/%s" % (
            urllib.request.__version__,
            self.config.get("Connection", "nick"),
            self.config.get("Auth", "owner_nick"),
        )
        req.add_header("User-Agent", useragent)
        stats = urllib.request.urlopen(req).read().decode()

        loaded = False
        for line in self.ship_re.findall(stats):
            line = list(line)
            ship = {}
            for index, key in enumerate(self.keys):
                if line[index] in self.mapping:
                    line[index] = self.mapping[line[index]]
                elif line[index].isdigit():
                    line[index] = int(line[index])
                if line[index] not in ("-", "",) and key not in self.skip:
                    ship[key] = line[index]
            ship["total_cost"] = ship["metal"] + ship["crystal"] + ship["eonium"]
            if ship["type"] == "EMP":
                ship["type"] = "Emp"
            elif ship["type"] == "Cloak":
                ship["type"] = "Norm"
                ship["is_cloaked"] = True
            if ship["is_cloaked"] == "Y":
                ship["is_cloaked"] = True
            # Assume TT-4.
            ship["eta"] -= 4
            fields = ["round"]
            params = [round]
            for key in ship:
                fields.append(key)
                params.append(ship[key])
            query = "INSERT INTO ship(%s) VALUES(%s)" % (", ".join(fields),
                                                         ", ".join(len(params) * ["%s"]))
            self.cursor.execute(query, tuple(params))
            loaded = True
        return loaded
