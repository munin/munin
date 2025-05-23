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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

# This work is Copyright (C)2006 by Andreas Jacobsen
# Individual portions may be copyright by individual contributors, and

# are included in this collective work with permission of the copyright
# owners.

# Nothing ascendancy/jester specific found here.
# qebab, 24/6/08.

import re
from munin import loadable


class whois(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(r"^\s*(\S+)")
        self.usage = self.__class__.__name__ + ""
        self.helptext = None

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        search = m.group(1)

        if search.lower() == self.config.get("Connection", "nick").lower():
            irc_msg.reply("I am Munin. Hear me roar.")
            return 1

        minimum_userlevel = 100
        r = self.load_user_from_pnick(
            search, irc_msg.round, minimum_userlevel=100
        )
        if not r:
            r = self.load_user_from_pnick(
                search, irc_msg.round, minimum_userlevel=1
            )
        reply = ""

        if not r:
            reply += "No members or galmates matching '%s'" % (search,)
        else:
            if r.userlevel < 100:
                reply += "No members matching '%s', but did find a galmate. " % (search,)
            if r:
                iswas = "was" if r.userlevel < 100 else "is"
                if r.pnick == irc_msg.user:
                    subject = "You"
                    possessive = "Your"
                    reply += "You are"
                else:
                    subject = "They"
                    possessive = "Their"
                    reply += "Information about"
                reply += " %s." % (r.pnick,)
                if r.alias_nick:
                    reply += " %s are also known as %s." % (subject, r.alias_nick,)
                if r.sponsor:
                    reply += " %s daddy %s %s. %s Munin number %s %s." % (
                        possessive, iswas, r.sponsor,
                        possessive, iswas, self.munin_number_to_output(r),
                    )
                reply += " %s have %d %s." % (
                    subject, r.carebears, self.pluralize(r.carebears, "carebear"),
                )
                if r.userlevel >= 100:
                    reply += " %s are%s a lemming." % (
                        subject, "" if r.lemming else " not",
                    )
                    query = """
                    SELECT u.pnick AS proposer, i.comment_text
                    FROM invite_proposal AS i
                    INNER JOIN user_list AS u on u.id = i.proposer_id
                    WHERE i.person = %s
                    AND i.vote_result = 'yes'
                    ORDER BY i.id DESC
                    LIMIT 1
                    """
                    self.cursor.execute(query, (r.pnick,))
                else:
                    query = """
                    SELECT u.pnick AS proposer, k.comment_text
                    FROM kick_proposal AS k
                    INNER JOIN user_list AS u on u.id = k.proposer_id
                    INNER JOIN user_list on user_list.id = k.person_id
                    WHERE k.person_id = %s
                    AND k.vote_result = 'yes'
                    ORDER BY k.id DESC
                    LIMIT 1
                    """
                    self.cursor.execute(query, (r.id,))
                i = self.cursor.fetchone()
                if i:
                    reply += " %s were prop %sed by %s with comment: %s" % (
                        subject,
                        "kick" if r.userlevel < 100 else "invit",
                        i['proposer'],
                        i['comment_text'],
                    )
                else:
                    reply += " Could not find %s most recent %s prop." % (
                        possessive.lower(),
                        "invite" if r.userlevel >= 100 else "kick",
                    )

        irc_msg.reply(reply)
        return 1

    def munin_number_to_output(self, u):
        number = u.munin_number(self.cursor, self.config)
        return number or "a kabajillion"
