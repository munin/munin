import math, re

class rprod(loadable.loadable):
    """Find out how much you can spend with n factories
    in m ticks."""

    def __init__(self, client, conn, cursor):
        
        loadable.loadable.__init__(self, client, conn, cursor, 1)
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
        
        while not close(guess, f(guess)):
            guess = f(guess)
        return guess

    def newton(self, f, guess):
        """Generic equation solver using newtons method."""
        
        return self.fixed_point(self.newton_transform(f),
                                guess)

    def pu(self, x):
        """Production units."""
        
        return 2 * math.sqrt * math.log(x, math.e)

    def rpu(self, y):
        """Curry it."""
        
        return lambda x: self.pu(x) - y

    def revprod(self, ticks, facs):
        """Reversed production formula."""
        
        output = (4000 * facs) ** 0.98
        return self.newton(self.rpu(ticks * output - 10000 * facs), 10)

    def execute(self, nick, username, host, target,
                prefix, command, user, access):

        match = self.commandre.search(command)

        if not match:
            return 0
        
        match = self.paramre.search(match.group(1))

        if not match:
            self.client.reply(prefix, nick, target,
            "Usage: %s, how much you can spend with n factories in m ticks."
                              % self.usage)
            return 0

        if access < self.level:
            self.client.reply(prefix, nick, target,
            "You do not have the access necessary to use this command.")
            return 0

        shipname = match.group(1)
        ticks = int(match.group(2))
        factories = int(match.group(3))

        query = "SELECT * FROM ship WHERE name ILIKE %s ORDER BY id"

        self.cursor.execute(query, ("%s" + shipname + "%",))
        ship = self.cursor.dictfetchone()

        if not ship:
            self.client.reply(prefix, nick, target,
            "%s is not a ship." % shipname)
            return 0
        
        res = int(self.revprod(ticks, factories))
        ships = int(res / ship['total_cost'])
        feud_ships = int(res / (ship['total_cost'] * 0.85))
        
        self.client.reply(prefix, nick, target,
        "You can build %s %s in %d ticks, or \
%s %s in %d ticks with feudalism." % (self.format_value(ships),
                                      ship['name'], ticks,
                                      self.format_value(feud_ships),
                                      ship['name'], ticks))
    
        return 1
