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

    def __init__(self, cursor):

        super(self.__class__, self).__init__(cursor, 1)
        self.paramre = re.compile(
            r"^\s+(\d+(?:\.\d+)?[mk]?)\s+(\S+)\s+(\d+)(?:\s+(\d+))?"
        )
        self.usage = (
            self.__class__.__name__ + " <number> <shipname> <factories> [population]"
        )

        self.helptext = [
            "Calculate the amount of time"
            " it will take to prod <n>"
            " <ship> with <factories> and <population>."
        ]

    def calc(self, gov_bonus, gov_speed, cost, population, race_speed, factories):
        required = 2 * math.sqrt(cost * gov_bonus) * self.ln(cost * gov_bonus)
        output = int(
            (4000 * factories) ** 0.98
            * (1 + population / 100.0 + race_speed + gov_speed)
        )
        ticks = int(math.ceil(required + 10000 * factories) / output)
        return ticks

    def execute(self, user, access, irc_msg):

        match = irc_msg.match_command(self.commandre)
        if not match:
            return 0

        match = self.paramre.search(match.group(1))

        if not match:
            irc_msg.reply(
                "Usage: %s, production time of n ships with n factories and n population."
                % self.usage
            )
            return 0

        if access < self.level:
            irc_msg.reply("You do not have the access necessary to use this command.")
            return 0

        number = self.human_readable_number_to_integer(match.group(1))
        shipname = match.group(2)
        factories = int(match.group(3))
        population = min(int(match.group(4) or 0), 60)

        ship = self.get_ship_from_db(shipname, irc_msg.round)
        if not ship:
            irc_msg.reply("%s is not a ship." % shipname)
            return 0

        race_speed = self.config.getfloat(
            "Planetarion", ship["race"].lower()[0:3] + "_prod_speed"
        )
        cost = number * ship["total_cost"]

        # All governments can have their own production speed and cost
        # reduction.
        corp_time = self.calc(
            gov_bonus=1
            - self.config.getfloat("Planetarion", "corporatism_cost_reduction"),
            gov_speed=self.config.getfloat("Planetarion", "corporatism_prod_speed"),
            cost=cost,
            population=population,
            race_speed=race_speed,
            factories=factories,
        )

        soci_time = self.calc(
            gov_bonus=1
            - self.config.getfloat("Planetarion", "socialism_cost_reduction"),
            gov_speed=self.config.getfloat("Planetarion", "socialism_prod_speed"),
            cost=cost,
            population=population,
            race_speed=race_speed,
            factories=factories,
        )

        nati_time = self.calc(
            gov_bonus=1
            - self.config.getfloat("Planetarion", "nationalism_cost_reduction"),
            gov_speed=self.config.getfloat("Planetarion", "nationalism_prod_speed"),
            cost=cost,
            population=population,
            race_speed=race_speed,
            factories=factories,
        )

        demo_time = self.calc(
            gov_bonus=1
            - self.config.getfloat("Planetarion", "democracy_cost_reduction"),
            gov_speed=self.config.getfloat("Planetarion", "democracy_prod_speed"),
            cost=cost,
            population=population,
            race_speed=race_speed,
            factories=factories,
        )

        tota_time = self.calc(
            gov_bonus=1
            - self.config.getfloat("Planetarion", "totalitarianism_cost_reduction"),
            gov_speed=self.config.getfloat("Planetarion", "totalitarianism_prod_speed"),
            cost=cost,
            population=population,
            race_speed=race_speed,
            factories=factories,
        )

        anar_time = self.calc(
            gov_bonus=1 - self.config.getfloat("Planetarion", "anarchy_cost_reduction"),
            gov_speed=self.config.getfloat("Planetarion", "anarchy_prod_speed"),
            cost=cost,
            population=population,
            race_speed=race_speed,
            factories=factories,
        )

        reply = (
            "Producing %s %s (%s) with %d factories and %d population takes %d ticks with Corporatism, "
            % (
                self.format_real_value(number),
                ship["name"],
                self.format_value(ship["total_cost"] * number),
                factories,
                population,
                corp_time,
            )
        )
        reply += (
            "%d ticks with Socialism, %d ticks with Nationalism, %d ticks with Democracy, %d ticks with Totalitarianism, %d ticks with Anarchy."
            % (soci_time, nati_time, demo_time, tota_time, anar_time)
        )

        irc_msg.reply(reply)

        return 1
