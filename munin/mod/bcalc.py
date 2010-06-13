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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and

# are included in this collective work with permission of the copyright
# owners.



import re
import string
from munin import loadable

class bcalc(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,1)
        self.paramre=re.compile(r"^\s+(\S+)")
        self.usage=self.__class__.__name__ + ""
	self.helptext=None

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        bcalc = ["http://bcalc.thrud.co.uk/","http://www.clawofdarkness.com/pawiki","http://bcalc.lch-hq.org/index.php",
                 "http://parser.5th-element.org/","http://munin.ascendancy.tv/",
                 "http://pa.xqwzts.com/prod.aspx","http://www.everyday-hero.net/reshack.html",
                 "http://patools.thrud.co.uk/", "http://game.planetarion.com/bcalc.pl"]

        reply="Bcalcs: "+string.join(bcalc," | ")
        irc_msg.reply(reply)

        return 1
