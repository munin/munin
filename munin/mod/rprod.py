
# Nothing alliance specific in here.
# qebab, 24/6/08.

import re
from munin import loadable

class rprod(loadable.loadable):
    """Find out how much you can spend with n factories
    in m ticks."""

    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,1)
        self.paramre = re.compile(r"^\s+(\S+)\s+(\d+)\s+(\d+)")
        self.usage = (self.__class__.__name__ +
                      " <ship> <ticks> <factories>.")

        self.helptext = ["Calculate how many <ship>"
                         " you can build in <ticks> "
                         "with <factories>."]

        self.dx = self.tolerance = 0.00001

    def derive(self, f):
        """Numerical derivation of the function f."""

        return lambda x: (f(x + self.dx) - f(x)) / self.dx

    def close(self, a, b):
        """Is the result acceptable?"""

        return abs(a - b) < self.tolerance

    def newton_transform(self, f):
        """Do a newton transform of the function f."""

        return lambda x: x - (f(x) / self.derive(f)(x))

    def fixed_point(self, f, guess):
        """Fixed point search."""

        while not self.close(guess, f(guess)):
            guess = f(guess)
        return guess

    def newton(self, f, guess):
        """Generic equation solver using newtons method."""

        return self.fixed_point(self.newton_transform(f),
                                guess)

    def rpu(self, y, math):
        """Curry it."""

        return lambda x: 2 * math.sqrt(x) * math.log(x, math.e) - y

    def revprod(self, ticks, facs):
        """Reversed production formula."""

        import math
        output = (4000 * facs) ** 0.98
        return self.newton(self.rpu(ticks * output - 10000 * facs, math), 10)

    def execute(self,user,access,irc_msg):
        match=irc_msg.match_command(self.commandre)
        if not match:
            return 0

        match = self.paramre.search(match.group(1))

        if not match:
            irc_msg.reply("Usage: %s, how much you can spend with n factories in m ticks."
                          % self.usage)
            return 0

        if access < self.level:
            irc_msg.reply("You do not have the access necessary to use this command.")
            return 0

        shipname = match.group(1)
        ticks = int(match.group(2))
        factories = int(match.group(3))

        query = "SELECT * FROM ship WHERE name ILIKE %s ORDER BY id"

        self.cursor.execute(query, ("%" + shipname + "%",))
        ship = self.cursor.dictfetchone()

        if not ship:
            irc_msg.reply("%s is not a ship." % shipname)
            return 0

        res = int(self.revprod(ticks, factories))
        ships = int(res / ship['total_cost'])
        feud_ships = int(res / ((ship['total_cost'] * (1-float(self.config.get('Planetarion', 'feudalism')))) / 1.2))

        irc_msg.reply("You can build %s %s (%s) in %d ticks, or \
%s %s in (%s) %d ticks with feudalism." % (self.format_value(ships * 100),
                                           ship['name'], self.format_value(ships * ship['total_cost']),
                                           ticks, self.format_value(feud_ships * 100),
                                           ship['name'], self.format_value(feud_ships * ship['total_cost']),
                                           ticks))

        return 1
