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

# This work is Copyright (C)2018 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

import re
from munin import loadable
from crontab import CronTab


class hugin(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1000)
        self.paramre = re.compile(r"^\s*(fly|roost|start|stop|status)?\s*$")
        self.usage = self.__class__.__name__ + " [start|stop|status]"
        self.helptext = [
            "Allows you to stop, start or view the status of hugin, the dumpfile loader."
        ]

    def start(self, ctab, irc_msg):
        job = ctab[0]
        if job.is_enabled():
            irc_msg.reply("Hugin is already spying")
        else:
            job.enable()
            ctab.write()
            irc_msg.reply("Hugin has been sent spying on the universe")

    def stop(self, ctab, irc_msg):
        job = ctab[0]
        if job.is_enabled():
            job.enable(False)
            ctab.write()
            irc_msg.reply("Hugin has been called home to rest")
        else:
            irc_msg.reply("Hugin is already resting at home")

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        cmd = m.group(1)
        ctab = CronTab(user=True)

        if not cmd or cmd == "status":
            irc_msg.reply(
                "Hugin is %s" % (["home resting", "out spying"][ctab[0].is_enabled()],)
            )
        elif access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
        elif cmd == "start" or cmd == "fly":
            return self.start(ctab, irc_msg)
        elif cmd == "stop" or cmd == "roost":
            return self.stop(ctab, irc_msg)
        else:
            irc_msg.reply("Usage: %s" % (self.usage,))
        return 0
