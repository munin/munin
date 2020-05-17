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
from munin import loadable


class rollback(loadable.loadable):
    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 1000)
        self.paramre = re.compile(r"^\s+([1-9][0-9]*)")
        self.selectre = re.compile(r"^SELECT [^ ]+ FROM")
        self.usage = self.__class__.__name__ + " <tick>"
        self.helptext = [
            "Remove all tick information from the given tick from the database. Only the latest tick may be removed."
        ]

    def delete_if_any(self, select_query, args_tuple):
        """Delete the rows returned by the given SELECT query and arguments.

        If the SELECT query returns without any results, do nothing and return
        1, Otherwise, DELETE them. If the deletion somehow fails to delete any
        rows, after we've already determined there are some to delete, ROLLBACK
        the active transaction and return 0. Otherwise, return 1.

        This function leaks its exceptions.

        """
        # print("Select query: %s" %(select_query,))
        self.cursor.execute(select_query, args_tuple)
        if self.cursor.rowcount > 0:
            delete_query = self.selectre.sub("DELETE FROM", select_query)
            # print("Delete query: %s" %(delete_query,))
            self.cursor.execute(delete_query, args_tuple)
            if self.cursor.rowcount < 1:
                self.cursor.execute("ROLLBACK")
                return 0
        # else:
        #     print("Nothing to delete from %s..."%(from_table,))
        return 1

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0

        m = self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        from_tick = int(m.group(1))
        to_tick = self.current_tick(irc_msg.round)

        if access < self.level:
            irc_msg.reply("You do not have enough access to time travel")
            return 0

        if from_tick > to_tick:
            irc_msg.reply(
                "It's tick %s, tick %s hasn't occurred yet. What are you trying to achieve?"
                % (to_tick, from_tick,)
            )
            return 0

        if from_tick != to_tick:
            irc_msg.reply(
                "That's way too many ticks to remove at once, go one at a time"
            )
            # We ask for a tick (even though only 1 value is valid) because the
            # last thing we need is a command that deletes data if you don't
            # pass it any arguments.
            return 0

        # Make sure we don't delete /half/ ticks...
        self.cursor.execute("BEGIN")

        try:

            query = "SELECT id FROM fleet_content"
            query += " WHERE fleet_id IN ("
            query += "     SELECT id FROM fleet"
            query += "     WHERE round = %s"
            query += "     AND launch_tick >= %s"
            query += " )"
            if not self.delete_if_any(query, (irc_msg.round, from_tick,)):
                return 0

            scan_tables = [
                "planet",
                "development",
                "unit",
                "au",
                "covop",
                "fleet",
            ]
            for scan_table in scan_tables:
                query = "SELECT id FROM %s" % (scan_table,)
                query += " WHERE scan_id IN ("
                query += "     SELECT id FROM scan"
                query += "     WHERE round = %s"
                query += "     AND tick >= %s"
                query += " )"
                if not self.delete_if_any(query, (irc_msg.round, from_tick,)):
                    return 0

            # Information in the user feed is not reported in the dumps until
            # the tick /after/ they occur. Therefore, we must delete one
            # additional tick of information from tables that source data from
            # the user feed.
            userfeed_tables = [
                "alliance_relation",
                "anarchy",
            ]
            for userfeed_table in userfeed_tables:
                query = "SELECT start_tick FROM %s" % (userfeed_table)
                query += " WHERE round = %s"
                query += " AND start_tick >= %s - 1"
                if not self.delete_if_any(query, (irc_msg.round, from_tick,)):
                    return 0

            query = "SELECT launch_tick FROM fleet"
            query += " WHERE round = %s"
            query += " AND launch_tick >= %s"
            if not self.delete_if_any(query, (irc_msg.round, from_tick,)):
                return 0

            tick_tables = [
                "scan",
                "fleet_log",
                "target",
                "planet_dump",
                "galaxy_dump",
                "alliance_dump",
                "userfeed_dump",
                "updates",
            ]
            for tick_table in tick_tables:
                query = "SELECT tick FROM %s" % (tick_table,)
                query += " WHERE round = %s"
                query += " AND tick >= %s"
                if not self.delete_if_any(query, (irc_msg.round, from_tick,)):
                    return 0

        except Exception as e:
            # Whatever went wrong, never leave a transaction open.
            try:
                self.cursor.execute("ROLLBACK")
            except:
                pass
            raise

        self.cursor.execute("COMMIT")

        irc_msg.reply("Successfully rolled back latest tick (%s)" % (from_tick,))

        return 1
