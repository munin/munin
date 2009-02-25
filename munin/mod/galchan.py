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

# This module has nothing alliance specific as far as I can tell.
# qebab, 24/6/08.

from munin import loadable

class galchan(loadable.loadable):
    def __init__(self,cursor):
        loadable.loadable.__init__(self,cursor,100)
        self.paramre=re.compile(r"^\s+(#\S+)")
        self.usage=self.__class__.__name__ + " <chan> "
        self.helptext=["This command adds Munin to the designated channel as a galchannel. The access of commands is limited to 1 in that channel (so you don't accidentally do !intel or something 'important'. You must make sure to add Munin to the channel _before_ you perform this command. If you fuck up and add the wrong channel, fuck you because then an HC has to manually remove it for you."]

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to add galchannels")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        chan=m.group(1).lower()



        query="INSERT INTO channel_list (chan,userlevel,maxlevel) VALUES (%s,1,1)"

        try:
            self.cursor.execute(query,(chan,))
            if self.cursor.rowcount>0:
                #irc_msg.reply("Added chan %s at level %s" % (chan,access_lvl))
                irc_msg.reply("Added your galchannel as %s (if you didn't add me to the channel with at least access 24 first, I'm never going to bother joining)" % (chan,))
                irc_msg.client.privmsg('P',"set %s autoinvite on" %(chan,));
                irc_msg.client.privmsg('P',"invite %s" %(chan,));

        except psycopg.IntegrityError:
            irc_msg.reply("Channel %s already exists" % (chan,))
            return 0
        except:
            raise

        return 1
