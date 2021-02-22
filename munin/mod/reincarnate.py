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
from configparser import NoSectionError, NoOptionError
from configupdater import ConfigUpdater
from munin import loadable
from munin.reboot import reboot

class reincarnate(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1000)
        self.paramre = re.compile(r"")
        self.usage = self.__class__.__name__ + ""
        self.helptext = [
            "Reboot me"
        ]

    def execute(self, user, access, irc_msg):
        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        irc_msg.reply("ARISING FROM THE DEAD")
        raise reboot()
