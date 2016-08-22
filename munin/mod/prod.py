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
        population = min(int(match.group(4) or 0), 60)

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

        race=ship['race'].lower()[0:3]
        race_speed = self.config.getfloat('Planetarion', race + '_prod_speed')

        if not ship:
            irc_msg.reply("%s is not a ship." % shipname)
            return 0

        cost = number * ship['total_cost']
        base_required = 2 * math.sqrt(cost) * self.ln(cost)

        reply = "Producing %s %s (%s) with %d factories and %d population takes " % (
            self.format_value(number * 100),
            ship['name'],
            self.format_value(ship['total_cost'] * number),
            factories,
            population)

        # All governments can have their own production speed and cost
        # reduction. Corporatism:
        corp_bonus = 1-self.config.getfloat('Planetarion', 'corporatism_cost_reduction')
        corp_speed = self.config.getfloat('Planetarion', 'corporatism_prod_speed')
        corp_required = 2 * math.sqrt(cost * corp_bonus) * self.ln(cost * corp_bonus)
        corp_output = int((4000 * factories) ** 0.98 * (1 + population/100.0 + race_speed + corp_speed))
        corp_time = int(math.ceil(corp_required + 10000 * factories) / corp_output)
        reply += "%d ticks with Corporatism" % (corp_time)

        # Socialism:
        soci_bonus = 1-self.config.getfloat('Planetarion', 'socialism_cost_reduction')
        soci_speed = self.config.getfloat('Planetarion', 'socialism_prod_speed')
        soci_required = 2 * math.sqrt(cost * soci_bonus) * self.ln(cost * soci_bonus)
        soci_output = int((4000 * factories) ** 0.98 * (1 + population/100.0 + race_speed + soci_speed))
        soci_time = int(math.ceil(soci_required + 10000 * factories) / soci_output)
        reply += ", %d ticks with Socialism" % (soci_time)

        # Nationalism:
        nati_bonus = 1-self.config.getfloat('Planetarion', 'nationalism_cost_reduction')
        nati_speed = self.config.getfloat('Planetarion', 'nationalism_prod_speed')
        nati_required = 2 * math.sqrt(cost * nati_bonus) * self.ln(cost * nati_bonus)
        nati_output = int((4000 * factories) ** 0.98 * (1 + population/100.0 + race_speed + nati_speed))
        nati_time = int(math.ceil(nati_required + 10000 * factories) / nati_output)
        reply += ", %d ticks with Nationalism" % (nati_time)

        # Democracy:
        demo_bonus = 1-self.config.getfloat('Planetarion', 'democracy_cost_reduction')
        demo_speed = self.config.getfloat('Planetarion', 'democracy_prod_speed')
        demo_required = 2 * math.sqrt(cost * demo_bonus) * self.ln(cost * demo_bonus)
        demo_output = int((4000 * factories) ** 0.98 * (1 + population/100.0 + race_speed + demo_speed))
        demo_time = int(math.ceil(demo_required + 10000 * factories) / demo_output)
        reply += ", %d ticks with Democracy" % (demo_time)

        # Totalitarianism:
        tota_bonus = 1-self.config.getfloat('Planetarion', 'totalitarianism_cost_reduction')
        tota_speed = self.config.getfloat('Planetarion', 'totalitarianism_prod_speed')
        tota_required = 2 * math.sqrt(cost * tota_bonus) * self.ln(cost * tota_bonus)
        tota_output = int((4000 * factories) ** 0.98 * (1 + population/100.0 + race_speed + tota_speed))
        tota_time = int(math.ceil(tota_required + 10000 * factories) / tota_output)
        reply += ", %d ticks with Totalitarianism" % (tota_time)

        # Anarchy:
        anar_bonus = 1-self.config.getfloat('Planetarion', 'anarchy_cost_reduction')
        anar_speed = self.config.getfloat('Planetarion', 'anarchy_prod_speed')
        anar_required = 2 * math.sqrt(cost * anar_bonus) * self.ln(cost * anar_bonus)
        anar_output = int((4000 * factories) ** 0.98 * (1 + population/100.0 + race_speed + anar_speed))
        anar_time = int(math.ceil(anar_required + 10000 * factories) / anar_output)
        reply += ", %d ticks with Anarchy." % (anar_time)

        irc_msg.reply(reply)

        return 1
