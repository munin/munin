"""
Loadable.Loadable subclass
"""

# This module doesn't have anything alliance specific as fas as I can tell.
# qebab, 24/6/08.

import re
from munin import loadable


class quitter(loadable.loadable):
    def __init__(self, cursor):
        super(self.__class__, self).__init__(cursor, 1)
        self.paramre = re.compile(r"^\s+(\S+)")
        self.usage = self.__class__.__name__ + " <nick>"
        self.helptext = None

    def execute(self, user, access, irc_msg):
        m = irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        quit = m.group(1)

        # do stuff here
        query = "SELECT pnick, quit FROM user_list WHERE pnick ILIKE %s"
        self.cursor.execute(query, ("%" + quit + "%",))

        reply = ""

        if self.cursor.rowcount == 0:
            reply = "'%s' doesn't match any users" % (quit,)
        else:
            r = self.cursor.dictfetchone()
            pnick = r["pnick"]
            count = r["quit"]
            query = "UPDATE user_list SET quit = quit + 1 WHERE pnick = %s"
            self.cursor.execute(query, (pnick,))
            reply = "That whining loser %s has now quit %d times." % (pnick, count + 1)
        irc_msg.reply(reply)

        return 1
