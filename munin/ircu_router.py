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

from .listener import auth
from .listener import command
from .listener import custom_runner
from . import mod
import psycopg2
import psycopg2.extras


class ircu_router(object):
    def __init__(self, client, config, loader):

        self.client = client
        self.config = config
        self.conn = self.create_db_connection(config)
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        self.listeners = [
            command.command(client, self.cursor, mod, loader, config),
            custom_runner.custom_runner(client, self.cursor, config),
            auth.auth(client, config),
        ]

    def run(self):
        while True:
            line = self.client.rline()
            if not line:
                break
            self.trigger_listeners(line)

    def trigger_listeners(self, line):
        for l in self.listeners:
            l.message(line)

    def create_db_connection(self, config):
        dsn = "user=%s dbname=%s" % (
            config.get("Database", "user"),
            config.get("Database", "dbname"),
        )
        if config.has_option("Database", "password"):
            dsn += " password=%s" % config.get("Database", "password")
        if config.has_option("Database", "host"):
            dsn += " host=%s" % config.get("Database", "host")

        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        return conn
