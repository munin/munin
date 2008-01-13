"""
loadable.loadable subclass.
"""

import math, re

class prod(loadable.loadable):
    """Mod for calculating the production time of a spend."""

    def __init__(self, client, conn, cursor):

        loadable.loadable.__init__(self, client, conn, cursor, 1)
        self.paramre = re.compile(r"^\s+(\d+[mk]?)\s+(\S+)\s+(\d+)")
        self.usage = (self.__class__.__name__ +
                      " <number> <shipname> <factories>")
        
        self.helptext = ["Calculate the amount of time"
                         " it will take to prod <n>"
                         " <ship> with <factories>."]

    def execute(self, nick, username, host, target, prefix,
                command, user, access):

        match = self.commandre.search(command)

        if not match:
            return 0

        match = self.paramre.search(match.group(1))
        
        if not match:
            self.client.reply(prefix, nick, target,
            "Usage: %s, production time of n ships with n factories."
                              % self.usage)
            return 0

        if access < self.level:
            self.client.reply(prefix, nick, target,
            "You do not have the access necessary to use this command.")
            return 0
            
        number = match.group(1)
        shipname = match.group(2)
        factories = match.group(3)
        
        if number[-1].lower() == 'k':
            number = int(number[:-1]) * 1000
        elif number[-1].lower() == 'm':
            number = int(number[:-1]) * (10 ** 6)
        else:
            number = int(number)

        factories = int(factories)

        # Verify or fix this!
        
        query = "SELECT * FROM ship WHERE name ILIKE %s ORDER BY id"

        self.cursor.execute(query, ("%" + shipname + "%",))
        ship = self.cursor.dictfetchone()

        if not ship:
            self.client.reply(prefix, nick, target,
            "%s is not a ship." % shipname)
            return 0

        def ln(n):
            """Natural logarithm."""

            return math.log(n, math.e)

        cost = number * ship['total_cost']
        required = 2 * math.sqrt(cost) * ln(cost)
        
        # For the gay cost bonus of feudalism
        feud_required = 2 * math.sqrt(cost * 0.85) * ln(cost * 0.85)
        
        output = int((4000 * factories) ** 0.98)

        norm_time = int(math.ceil((required +
                                   (10000 * factories)) / output))
        feud_time = int(math.ceil((feud_required +
                                   (10000 * factories)) / output))
        
        reply = "The base time for producing %s %s (%s) is %s ticks. " % (self.format_value(number),
                                                                          ship['name'],
                                                                          self.format_value(ship['total_cost'] * number * 0.01),
                                                                          norm_time)
        reply += "With feudalism it is %s ticks." % feud_time

        self.client.reply(prefix, nick, target, reply)

        return 1
        
