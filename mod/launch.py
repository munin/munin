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


class launch(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,1)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+|\d+)\s+(\d+)")
        self.usage=self.__class__.__name__ + " <class|eta> <land_tick>"
        self.helptext=["Calculate launch tick, launch time, prelaunch tick and prelaunch modifier for a given ship class or eta, and land tick."]

        self.class_eta = {"fi": 8,
                          "co": 8,
                          "fr": 9,
                          "de": 9,
                          "cr": 10,
                          "bs": 10}

    def execute(self,nick,host,target,prefix,command,user,access,irc_msg):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0


        eta = m.group(1)
        land_tick = int(m.group(2))

        if eta.lower() in self.class_eta.keys():
             eta = self.class_eta[eta.lower()]
        else:
            try:
                eta = int(eta)
            except ValueError:
                irc_msg.reply("Usage: %s" % (self.usage,))
                return 0

        query="SELECT max_tick()"
        try:
            self.cursor.execute(query)
            current_tick = self.cursor.dictfetchone()
        except psycopg.IntegrityError:
            irc_msg.reply("Could not fetch current tick.")
            return 0
        current_tick = current_tick['max_tick']

        current_time = datetime.datetime.utcnow()
        launch_tick = land_tick - eta
        launch_time = current_time + datetime.timedelta(hours=(launch_tick-current_tick))
        prelaunch_tick = land_tick - eta + 1
        prelaunch_mod = launch_tick - current_tick

        irc_msg.reply("eta %d landing pt %d (currently %d) must launch at pt %d (%s), or with prelaunch tick %d (currently %+d)" % (eta, land_tick, current_tick, launch_tick, (launch_time.strftime("%m-%d %H:55")), prelaunch_tick, prelaunch_mod))

        return 1
