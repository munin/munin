import math, re

class rprod(loadable.loadable):
    """Find out how much you can spend with n factories
    in m ticks."""

    def __init__(self, client, conn, cursor):
        
        loadable.loadable.__init__(self, client, conn, cursor, 1)
        self.paramre = re.compile(r"^\s+(\d+)\s+(\d+)")
        self.usage = (self.__class__.__name__ +
                      " <ticks> <factories>.")

        self.helptext = ["Calculate how much resource"
                         " you can spend in n ticks "
                         "with m factories."]

        self.dx = self.tolerance = 0.00001
        
    def derive(self, f):

        return lambda x: (f(x + self.dx) - f(x)) / self.dx

    def close(self, a, b):

        return abs(a - b) < self.tolerance

    def newton_transform(self, f):

        return lambda x: x - (f(x) / self.derive(f)(x))

    def fixed_point(self, f, guess):

        while not close(guess, f(guess)):
            guess = f(guess)
        return guess

    def newton(self, f, guess):

        return self.fixed_point(self.newton_transform(f),
                                guess)

    def pu(self, x):

        return 2 * math.sqrt * math.log(x, math.e)

    def rpu(self, y):

        return lambda x: self.pu(x) - y

    def revprod(self, ticks, facs):

        output = (4000 * facs) ** 0.98
        return self.newton(self.rpu(ticks * output - 10000 * facs), 10)

    def execute(self, nic, username, host, target,
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

        ticks = int(match.group(1))
        factories = int(match.group(2))

    
        res = int(self.revprod(ticks, factories))

        self.client.reply(prefix, nick, target,
        "In %d ticks you can produce %s resources with %d factories" % (
            ticks, self.format_value(res), factories))

        return 1
