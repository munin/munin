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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

# This module doesn't have anything alliance specific as far as I can tell.
# qebab, 24/6/08.

import re
import psycopg2
from munin import loadable


class pref(loadable.loadable):
    def __init__(self, cursor):
        super().__init__(cursor, 1)
        self.paramre = re.compile(r"^\s*(.*)")
        self.usage = self.__class__.__name__ + " [option=value]+"
        self.helptext = [
            "Options: planet=x.y.z | password=OnlyWorksInPM | phone=+1-800-HOT-BIRD | pubphone=T|F | lemming=T|F | stay=T|F"
        ]

    def execute(self, user, access, irc_msg):

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        u = loadable.user(pnick=irc_msg.user)
        if not u.load_from_db(self.cursor, irc_msg.round):
            irc_msg.reply(
                "You must be registered to use the "
                + self.__class__.__name__
                + " command (log in with Q and set mode +x)"
            )
            return 1

        param_dict = self.split_opts(m.group(1))
        if param_dict is None:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 1

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        for opt in param_dict:
            val = param_dict[opt]
            if opt == "planet":
                m = self.planet_coordre.search(val)
                if m:
                    x = m.group(1)
                    y = m.group(2)
                    z = m.group(3)
                    self.save_planet(irc_msg, u, x, y, z, user)
                    self.save_lemming(irc_msg, u, "yes", access)
                else:
                    irc_msg.reply(
                        "You must provide coordinates (x:y:z) for the planet option"
                    )
            if opt == "stay":
                self.save_stay(irc_msg, u, val, access)
            if opt == "lemming":
                self.save_lemming(irc_msg, u, val, access)
            if opt == "pubphone":
                self.save_pubphone(irc_msg, u, val, access)
            if opt == "password":
                self.save_password(irc_msg, u, val)
            if opt == "phone":
                self.save_phone(irc_msg, u, val)

        return 1

    def save_planet(self, irc_msg, u, x, y, z, user):
        p = loadable.planet(x=x, y=y, z=z)
        if not p.load_most_recent(self.cursor, irc_msg.round):
            irc_msg.reply("%s:%s:%s is not a valid planet" % (x, y, z))
            return 0
        if u.pref:
            query = "INSERT INTO round_user_pref (user_id,round,planet_id) VALUES (%s,%s,%s)"
            query += " ON CONFLICT (user_id,round) DO"
            query += " UPDATE SET planet_id=EXCLUDED.planet_id"
            self.cursor.execute(query, (u.id, irc_msg.round, p.id,))
            irc_msg.reply("Your planet has been saved as %s:%s:%s" % (x, y, z))
            if p.id > 0 and u.userlevel >= 100:
                i = loadable.intel(pid=p.id)
                i.load_from_db(self.cursor, irc_msg.round)
                a = loadable.alliance(name=self.config.get("Auth", "alliance"))
                have_alliance = a.load_most_recent(self.cursor, irc_msg.round)
                if i.id:
                    arguments = (user,)
                    query = "UPDATE intel SET nick=%s"
                    if have_alliance:
                        arguments += (a.id,)
                        query += ",alliance_id=%s"
                    arguments += (i.id,)
                    query += " WHERE id=%s"
                else:
                    arguments = (p.id, user,)
                    query = "INSERT INTO intel (pid,nick,"
                    if have_alliance:
                        arguments += (a.id,)
                        query += "alliance_id,"
                    arguments += (irc_msg.round,)
                    query += "round) VALUES ({})".format(','.join(["%s"] * len(arguments)))
                self.cursor.execute(query, arguments)

    def save_stay(self, irc_msg, u, status, access):
        if access < 100:
            return 0
        query = ""
        args = ()
        if u.pref:
            query = "INSERT INTO round_user_pref (user_id,round,stay) VALUES (%s,%s,%s)"
            query += " ON CONFLICT (user_id,round) DO"
            query += " UPDATE SET stay=EXCLUDED.stay"
            args += (
                u.id,
                irc_msg.round,
                status,
            )
        reply = "Your stay status has been saved as %s" % (status,)
        try:
            self.cursor.execute(query, args)
        except psycopg2.ProgrammingError:
            reply = (
                "Your stay status '%s' is not a valid value. If you are staying for next round, it should be 'yes'. Otherwise it should be 'no'."
                % (status,)
            )
        irc_msg.reply(reply)

    def save_lemming(self, irc_msg, u, status, access):
        if access < 100:
            return 0
        query = ""
        args = ()
        if u.pref:
            query = (
                "INSERT INTO round_user_pref (user_id,round,lemming) VALUES (%s,%s,%s)"
            )
            query += " ON CONFLICT (user_id,round) DO"
            query += " UPDATE SET lemming=EXCLUDED.lemming"
            args += (
                u.id,
                irc_msg.round,
                status,
            )
        reply = "Your lemming status has been saved as %s" % (status,)
        try:
            self.cursor.execute(query, args)
        except psycopg2.ProgrammingError:
            reply = (
                "Your lemming status '%s' is not a valid value. If you wish to die a glorious death for the emperor, it should be 'yes'. Otherwise it should be 'no'."
                % (status,)
            )
        irc_msg.reply(reply)

    def save_phone(self, irc_msg, u, passwd):
        if len(passwd) > 32:
            irc_msg.reply(
                "Your phone number may not be longer than 32 characters (if you need more than 32 characters poke %s)."
                % (self.config.get("Auth", "owner_nick"))
            )
            return
        query = "UPDATE user_list SET phone = %s"
        query += " WHERE id = %s"

        self.cursor.execute(query, (passwd, u.id))
        if self.cursor.rowcount > 0:
            irc_msg.reply(
                "Updated your phone number. Remember to set your phone to public (!pref pubphone=yes) or allow some people to see your phone number (!phone allow stalker) or no one will be able to see your number."
            )
        else:
            irc_msg.reply("Something went wrong. Go whine to your sponsor.")

    def save_pubphone(self, irc_msg, u, status, access):
        if access < 100:
            alliance = (self.config.get("Auth", "alliance"),)
            irc_msg.reply(
                "Only %s members can allow all members of %s to view their phone"
                % (alliance, alliance)
            )
            return 0
        query = ""
        args = ()
        query = "UPDATE user_list SET pubphone=%s WHERE id=%s"
        args += (status, u.id)
        reply = "Your pubphone status has been saved as %s" % (status,)
        try:
            self.cursor.execute(query, args)
        except psycopg2.ProgrammingError:
            reply = (
                "Your pubphone status '%s' is not a valid value. If you want your phone number to be visible to all %s members, it should be 'yes'. Otherwise it should be 'no'."
                % (status, self.config.get("Auth", "alliance"))
            )
        irc_msg.reply(reply)

    def save_password(self, irc_msg, u, passwd):
        query = "UPDATE user_list SET passwd = MD5(MD5(salt) || MD5(%s))"
        query += " WHERE id = %s"

        m = re.match(r"(#\S+)", irc_msg.target, re.I)
        if m:
            irc_msg.reply("Don't set your password in public you shit")
        else:
            self.cursor.execute(query, (passwd, u.id))
            if self.cursor.rowcount > 0:
                irc_msg.reply("Updated your password")
            else:
                irc_msg.reply("Something went wrong. Go whine to your sponsor.")
