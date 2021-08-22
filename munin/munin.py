#!/usr/bin/python -u

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

import os
import configparser
import time

from .connection import connection

from .loader import Loader
import traceback
from . import reboot
import socket


class munin(object):
    ROUTER = "munin.%s_router"

    def __init__(self):
        config = configparser.ConfigParser()
        if not config.read("muninrc"):
            raise ValueError("Expected configuration in muninrc, not found.")

        self.loader = Loader()
        self.loader.populate("munin")
        self.router = self.loader.get_module(
            self.ROUTER % config.get("Connection", "type")
        )

        self.client = connection(config)
        self.client.connect()
        self.client.wline("NICK %s" % config.get("Connection", "nick"))
        self.client.wline(
            "USER %s 0 * : %s"
            % (config.get("Connection", "user"), config.get("Connection", "name"))
        )
        self.config = config

        while True:
            try:
                self.reboot()
                break
            except socket.error as s:
                print(
                    "Exception during command at %s: %s" % (time.asctime(), s.__str__())
                )
                traceback.print_exc()
                raise
            except socket.timeout as s:
                print(
                    "Exception during command at %s: %s" % (time.asctime(), s.__str__())
                )
                traceback.print_exc()
                raise
            except reboot.reboot:
                continue
            except Exception as e:
                print("Exception during command: " + e.__str__())
                traceback.print_exc()
                continue

    def reboot(self):
        print("Rebooting Munin.")
        self.config.read("muninrc")
        self.loader.populate("munin")
        self.loader.refresh()
        self.router = self.loader.get_module(
            self.ROUTER % self.config.get("Connection", "type")
        )
        router = self.router.router(self.client, self.config, self.loader)
        router.run()


def run():
    ofile = open("pid.munin", "w")
    ofile.write("%s" % (os.getpid(),))
    ofile.close()

    munin()
