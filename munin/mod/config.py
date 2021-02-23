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

class config(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1000)
        self.paramre = re.compile(r"^\s*(?:([^\s/ ]+)(?:/(\S+)(?:\s+(.+))?)?)?")
        self.usage = self.__class__.__name__ + " [<section>[/<option> [value]]"
        self.helptext = [
            "Read and write options from and to the configuration file"
        ]
        # Don't expose authentication information over IRC.
        self.hidden_options = [
            'IRC/auth',
            'Database/password',
            'clickatell/pass',
            'clickatell/api',
        ]
        self.hidden_sections = [
        ]

    def execute(self, user, access, irc_msg):
        if access < self.level:
            irc_msg.reply("You do not have enough access to load ship stats")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        section = m.group(1) or None
        option = m.group(2) or None
        value = m.group(3) or None

        if value:
            return self.set(irc_msg, section, option, value)
        elif option:
            success, value = self.get(irc_msg, section, option)
            if success:
                irc_msg.reply("Configuration option %s/%s has value: %s" % (section, option, value,))
                return 1
            else:
                return 0
        elif section:
            return self.get_options(irc_msg, section)
        else:
            return self.get_sections(irc_msg)

    def set(self, irc_msg, section, option, value):
        """Update option in Munin configuration file to the given value."""
        success, old_value = self.get(irc_msg, section, option)
        if success:
            new_value = type(old_value)(value)
            # ConfigParser supports writing out changed configuration files,
            # but does not preserve whitespace and comments. ConfigUpdater
            # does.
            updater = ConfigUpdater()
            updater.read("muninrc")
            updater[section][option] = new_value
            updater.update_file()
            irc_msg.reply("Updated configuration option %s/%s from '%s' to '%s', ARISING FROM THE DEAD" % (section, option, old_value, new_value,))
            raise reboot()
        else:
            return 0

    def get(self, irc_msg, section, option):
        """Return the value of the given option in the Munin configuration file."""
        path = "%s/%s" % (section, option,)
        if path in self.hidden_options:
            irc_msg.reply("Nope, this is a SECRET configuration value!")
        else:
            try:
                return (True, self.config.get(section, option),)
            except NoSectionError as nse:
                irc_msg.reply("Failed to find section %s" % (section,))
            except NoOptionError as noe:
                irc_msg.reply("Failed to find option %s in section %s" % (option, section,))
        return (False, None,)

    def get_options(self, irc_msg, section):
        """"""
        try:
            options = [o for o in self.config.options(section)
                       if "%s/%s" % (section, o,) not in self.hidden_options]
            irc_msg.reply("Available options in section %s: %s" % (section, ', '.join(options),))
            return 1
        except NoSectionError as nse:
            irc_msg.reply("Failed to find section %s" % (section,))
            return 0

    def get_sections(self, irc_msg):
        """"""
        sections = [s for s in self.config.sections()
                    if s not in self.hidden_sections]
        irc_msg.reply("Available sections in configuration file: %s" % (', '.join(sections),))
        return 1
