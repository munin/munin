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

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08
# I lied. Removed alliance specific things.
# qebab, 24/6/08.

import re
import string
from munin import loadable

class loosecunts(loadable.loadable):
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,100)
        self.paramre=re.compile(r"^(\s+(\S+))?")
        self.usage=self.__class__.__name__ + ""

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        search=irc_msg.user_or_nick()
        m=self.paramre.search(m.group(1))

        if m:
            search=m.group(2) or search

        for q in ["DROP TABLE epenis","DROP SEQUENCE xp_gain_rank",
                  "DROP SEQUENCE value_diff_rank","DROP SEQUENCE activity_rank"]:
            try:
                self.cursor.execute(q)
            except Exception:
                pass

        query="CREATE TEMP SEQUENCE xp_gain_rank;CREATE TEMP SEQUENCE value_diff_rank;CREATE TEMP SEQUENCE activity_rank"
        self.cursor.execute(query)
        query="SELECT setval('xp_gain_rank',1,false); SELECT setval('value_diff_rank',1,false); SELECT setval('activity_rank',1,false)"
        self.cursor.execute(query)

        query="CREATE TEMP TABLE epenis AS"
        query+=" (SELECT *,nextval('activity_rank') AS activity_rank"
        query+="  FROM (SELECT *,nextval('value_diff_rank') AS value_diff_rank"
        query+="        FROM (SELECT *,nextval('xp_gain_rank') AS xp_gain_rank"
        query+="              FROM (SELECT i.nick, u.pnick, p0.xp-p72.xp AS xp_gain, p0.score-p72.score AS activity, p0.value-p72.value AS value_diff"
        query+="                    FROM       planet_dump     AS p0"
        query+="                    LEFT JOIN  intel           AS i   ON p0.id=i.pid"
        query+="                    LEFT JOIN  round_user_pref AS r   ON p0.id=r.planet_id"
        query+="                    LEFT JOIN  user_list       AS u   ON u.id=r.user_id"
        query+="                    INNER JOIN planet_dump     AS p72 ON p0.id=p72.id AND p0.tick - 72 = p72.tick"
        query+="                    WHERE p0.tick = (SELECT max_tick(%s::smallint)) AND p0.round = %s"
        query+="                    ORDER BY xp_gain DESC) AS t6"
        query+="              ORDER BY value_diff DESC) AS t7"
        query+="        ORDER BY activity DESC) AS t8)"

        self.cursor.execute(query,(irc_msg.round,irc_msg.round,))

        query="SELECT nick,pnick,xp_gain,activity,value_diff,xp_gain_rank,value_diff_rank,activity_rank"
        query+=" FROM epenis"
        query+=" ORDER BY activity_rank DESC LIMIT 5"

        self.cursor.execute(query,())

        if self.cursor.rowcount < 1:
            irc_msg.reply("There is no penis")
            return 1

        prev=[]
        for b in self.cursor.dictfetchall():
            prev.append("%d:%s (%s)"%(b['activity_rank'],b['pnick'] or b['nick'],self.format_value(b['activity']*100)))
        reply="Loose cunts: %s"%(', '.join(prev))

        irc_msg.reply(reply)
        return 1

