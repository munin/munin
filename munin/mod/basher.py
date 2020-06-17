"""
Loadable.Loadable subclass
"""

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08

import re
from munin import loadable


class basher(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(.*)")
        self.usage = self.__class__.__name__ + " <x:y:z>"
        self.helptext = None

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0
        planet = None
        param = m.group(1)
        m = self.paramre.search(param)

        if not m or not m.group(1):
            u = loadable.user(pnick=irc_msg.user)
            if not u.load_from_db(self.cursor, irc_msg.round):
                irc_msg.reply(
                    "You must be registered to use the automatic "
                    + self.__class__.__name__
                    + " command (log in with P and set mode +x, then make sure you've set your planet with the pref command)"
                )
                #
                return 1
            if u.planet:
                planet = u.planet
            else:
                irc_msg.reply("Usage: %s" % (self.usage,))
                return 1
        else:
            m = self.coordre.search(param)
            if m:
                x = m.group(1)
                y = m.group(2)
                z = m.group(4)
                # assign param variables
                if z:
                    p = loadable.planet(x=x, y=y, z=z)
                    if not p.load_most_recent(self.cursor, irc_msg.round):
                        irc_msg.reply("No planet matching '%s' found" % (param,))
                        return 1
                    planet = p
            else:
                irc_msg.reply(
                    "Usage: %s (you must be registered for automatic lookup)"
                    % (self.usage,)
                )
                return 1
        if planet:
            reply = (
                "%s:%s:%s can hit planets with value %d or above or score %d or above"
                % (
                    planet.x,
                    planet.y,
                    planet.z,
                    int(planet.value * 0.4),
                    int(planet.score * 0.6),
                )
            )

        irc_msg.reply(reply)
        return 1
