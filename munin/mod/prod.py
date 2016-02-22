"""
loadable.loadable subclass.
"""

import math
import re

# This module doesn't have anything alliance specific.
# qebab, 24/6/08.

from munin import loadable

class prod(loadable.loadable):
    """Mod for calculating the production time of a spend."""

    def ln(self, n):
        """Natural logarithm."""
        return math.log(n, math.e)

    def __init__(self,cursor):

        super(self.__class__,self).__init__(cursor,1)
        self.paramre = re.compile(r"^\s+(\d+(?:\.\d+)?[mk]?)\s+(\S+)\s+(\d+)(?:\s+(\d+))?")
        self.usage = (self.__class__.__name__ +
                      " <number> <shipname> <factories> [population]")

        self.helptext = ["Calculate the amount of time"
                         " it will take to prod <n>"
                         " <ship> with <factories> and <population>."]

    def execute(self,user,access,irc_msg):

        match=irc_msg.match_command(self.commandre)
        if not match:
            return 0

        match = self.paramre.search(match.group(1))

        if not match:
            irc_msg.reply("Usage: %s, production time of n ships with n factories and n population." % self.usage)
            return 0

        if access < self.level:
            irc_msg.reply("You do not have the access necessary to use this command.")
            return 0

        number = match.group(1)
        shipname = match.group(2)
        factories = match.group(3)
        population = min(int(match.group(4)) or 0, 60)

        if number[-1].lower() == 'k':
            number = float(number[:-1]) * 1000
        elif number[-1].lower() == 'm':
            number = float(number[:-1]) * (10 ** 6)
        else:
            number = float(number)

        number = int(number)
        factories = int(factories)

        # Verify or fix this!
        ship=self.get_ship_from_db(shipname)

        if not ship:
            irc_msg.reply("%s is not a ship." % shipname)
            return 0

        cost = number * ship['total_cost']
        base_required = 2 * math.sqrt(cost) * self.ln(cost)
        output = int((4000 * factories) ** 0.98 * (1 + population/100))

        reply = "Producing %s %s (%s) with %d factories and %d population takes " % (
            self.format_value(number * 100),
            ship['name'],
            self.format_value(ship['total_cost'] * number),
            factories,
            population)

        # All governments can have their own production speed. Corporatism:
        corp_speed = 1-float(self.config.get('Planetarion', 'corporatism_prod_speed'))
        corp_time = int(corp_speed * math.ceil((base_required + (10000 * factories)) / output))
        reply += "%s ticks with Corporatism" % (corp_time)

        # Socialism:
        soci_speed = 1-float(self.config.get('Planetarion', 'socialism_prod_speed'))
        soci_time = int(soci_speed * math.ceil((base_required + (10000 * factories)) / output))
        reply += ", %s ticks with Socialism" % (soci_time)

        # Nationalism:
        nati_speed = 1-float(self.config.get('Planetarion', 'nationalism_prod_speed'))
        nati_time = int(nati_speed * math.ceil((base_required + (10000 * factories)) / output))
        reply += ", %s ticks with Nationalism" % (nati_time)

        # Democracy:
        demo_bonus = 1-float(self.config.get('Planetarion', 'democracy_cost_reduction'))
        demo_speed = 1-float(self.config.get('Planetarion', 'democracy_prod_speed'))
        demo_required = 2 * math.sqrt(cost * demo_bonus) * self.ln(cost * demo_bonus)
        demo_time = int(demo_speed * math.ceil((demo_required + (10000 * factories)) / output))
        reply += ", %s ticks with Democracy" % (demo_time)

        # Totalitarianism:
        tota_bonus = 1-float(self.config.get('Planetarion', 'totalitarianism_cost_reduction'))
        tota_speed = 1-float(self.config.get('Planetarion', 'totalitarianism_prod_speed'))
        tota_required = 2 * math.sqrt(cost * tota_bonus) * self.ln(cost * tota_bonus)
        tota_time = int(tota_speed * math.ceil((tota_required + (10000 * factories)) / output))
        reply += ", %s ticks with Totalitarianism" % (tota_time)

        # Anarchy:
        anar_speed = 1-float(self.config.get('Planetarion', 'anarchy_prod_speed'))
        anar_time = int(anar_speed * math.ceil((base_required + (10000 * factories)) / output))
        reply += ", %s ticks with Anarchy." % (anar_time)

        irc_msg.reply(reply)

        return 1
