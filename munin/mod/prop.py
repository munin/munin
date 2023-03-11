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


import re
from munin import loadable
import datetime


class prop(loadable.loadable):
    """
    foo
    """

    def __init__(self, cursor):
        super().__init__(cursor, 100)
        self.paramre = re.compile(
            r"^\s*(invite|kick|poll|list|show|vote|expire|cancel|recent|search)(.*)",
            re.I,
        )
        self.invite_kickre = re.compile(r"^\s+(\S+)(\s+(\S.*))", re.I)
        self.pollre = re.compile(r"\s*([^?]+)\?\s*([^?\"]+)", re.I)
        self.poll_split_answers = re.compile(r"\s*!+\s*")
        self.votere = re.compile(r"^\s+(\d+)\s+(.*)", re.I)
        self.usage = self.__class__.__name__ + (
            " [<invite|kick> <pnick> <comment>] |"
            " poll <question>? <answer>!... |"
            " [list] |"
            " [vote <number> <yes|no|abstain|A..J|[answer]>] |"
            " [expire <number>] |"
            " [show <number>] |"
            " [cancel <number>] |"
            " [recent] |"
            " [search <pnick>]"
        )
        self.helptext = [
            (
                "A proposition is a vote to do something. For now, you can raise propositions"
                " to invite or kick someone, or to perform a poll. Once raised the proposition"
                " will stand until you expire it.  Make sure you give everyone time to have "
                " their say. Votes for and against a proposition are weighted by carebears. You"
                " must have at least 1 carebear to vote."
            )
        ]

    def execute(self, user, access, irc_msg):

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        u = self.load_user(user, irc_msg)
        if not u:
            return 0

        m = self.paramre.search(irc_msg.command_parameters)
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        prop_type = m.group(1)

        if prop_type.lower() == "invite":
            if not self.config.getboolean("Alliance", "allow_prop_invites"):
                irc_msg.reply(
                    "No. If you want to invite someone, figure out a different way to make it happen."
                )
                return 1
            m = self.match_or_usage(irc_msg, self.invite_kickre, m.group(2))
            if not m:
                return 1
            if self.command_not_used_in_home(
                irc_msg, self.__class__.__name__ + " invite"
            ):
                return 1
            if self.too_many_members(irc_msg):
                return 1
            person = m.group(1).lower()
            comment = m.group(3).lower()
            self.process_invite_proposal(irc_msg, u, person, comment)

        elif prop_type.lower() == "kick":
            if not self.config.getboolean("Alliance", "allow_prop_kicks"):
                irc_msg.reply(
                    "No. If you want to kick someone, figure out a different way to make it happen."
                )
                return 1
            m = self.match_or_usage(irc_msg, self.invite_kickre, m.group(2))
            if not m:
                return 1
            if self.command_not_used_in_home(
                irc_msg, self.__class__.__name__ + " kick"
            ):
                return 1

            person = m.group(1).lower()
            comment = m.group(3).lower()
            self.process_kick_proposal(irc_msg, u, person, comment)

        elif prop_type.lower() == "poll":
            if not self.config.getboolean("Alliance", "allow_prop_polls"):
                irc_msg.reply(
                    "No. If you want to poll the alliance, figure out a different way to make it happen."
                )
                return 1
            m = self.match_or_usage(irc_msg, self.pollre, m.group(2))
            if not m:
                return 1
            if self.command_not_used_in_home(
                irc_msg, self.__class__.__name__ + " poll"
            ):
                return 1
            question = m.group(1)
            answers = [
                answer
                for answer in re.split(self.poll_split_answers, m.group(2))
                if len(answer) > 0
            ]
            self.process_poll_proposal(irc_msg, u, question, answers[:10])

        elif prop_type.lower() == "list":
            self.process_list_all_proposals(irc_msg, u)

        elif prop_type.lower() == "show":
            m = self.match_or_usage(irc_msg, re.compile(r"^\s*(\d+)"), m.group(2))
            if not m:
                return 1
            prop_id = int(m.group(1))
            self.process_show_proposal(irc_msg, u, prop_id)

        elif prop_type.lower() == "vote":
            m = self.match_or_usage(irc_msg, self.votere, m.group(2))
            if not m:
                return 1
            prop_id = int(m.group(1))
            vote = m.group(2).lower()
            self.process_vote_proposal(irc_msg, u, prop_id, vote)

        elif prop_type.lower() == "expire":
            m = self.match_or_usage(irc_msg, re.compile(r"\s*(\d+)"), m.group(2))
            if not m:
                return 1
            if self.command_not_used_in_home(
                irc_msg, self.__class__.__name__ + " expire"
            ):
                return 1
            prop_id = int(m.group(1))
            self.process_expire_proposal(irc_msg, u, prop_id)

        elif prop_type.lower() == "cancel":
            m = self.match_or_usage(irc_msg, re.compile(r"\s*(\d+)"), m.group(2))
            if not m:
                return 1
            if self.command_not_used_in_home(
                irc_msg, self.__class__.__name__ + " cancel"
            ):
                return 1
            prop_id = int(m.group(1))
            self.process_cancel_proposal(irc_msg, u, prop_id)

        elif prop_type.lower() == "recent":
            self.process_recent_proposal(irc_msg, u)

        elif prop_type.lower() == "search":
            m = self.match_or_usage(irc_msg, re.compile(r"\s*(\S+)"), m.group(2))
            if not m:
                return 1
            self.process_search_proposal(irc_msg, u, m.group(1).lower())
        return 1

    def too_many_members(self, irc_msg):
        members = loadable.user.count_members(self.cursor)
        limit = self.config.getint("Alliance", "member_limit")
        if members >= limit:
            irc_msg.reply(
                "You have tried to invite somebody, but we have %s losers and I can't be bothered dealing with more than %s of you."
                % (members, limit)
            )
            return 1
        return 0

    def process_invite_proposal(self, irc_msg, user, person, comment):
        if self.is_member(person):
            irc_msg.reply(
                "Stupid %s, that wanker %s is already a member." % (user.pnick, person)
            )
            return 1
        if self.is_already_an_alias(person):
            irc_msg.reply(
                "Dumb %s, %s is already someone's alias." %(user.pnick, person)
            )
            return 1
        if self.is_already_proposed_invite(person):
            irc_msg.reply(
                "Silly %s, there's already a proposal to invite %s."
                % (user.pnick, person)
            )
            return 1
        if user.has_ancestor(self.cursor, person, irc_msg.round):
            irc_msg.reply("Ew, incest.")
            return 1
        last_comp = self.was_recently_proposed("invite", person)
        prop_id = self.create_invite_proposal(user, person, comment, last_comp)
        reply = (
            "%s created a new proposition (nr. %d) to invite %s. When people have been"
            " given a fair shot at voting you can call a count using !prop expire %d. PLEASE"
            " MAKE SURE THAT THIS IS THE CORRECT NICKNAME!"
        ) % (
            user.pnick,
            prop_id,
            person,
            prop_id,
        )
        irc_msg.reply(reply)

    def process_kick_proposal(self, irc_msg, user, person, comment):
        p = self.load_user_from_pnick(person, irc_msg.round)
        if person.lower() == self.config.get("Connection", "nick").lower():
            irc_msg.reply("I'll peck your eyes out, cunt.")
            return 1
        if not p or p.userlevel < 100:
            irc_msg.reply(
                "Stupid %s, you can't kick %s, they're not a member."
                % (user.pnick, person)
            )
            return 1
        if self.is_already_proposed_kick(p.id):
            irc_msg.reply(
                "Silly %s, there's already a proposition to kick %s."
                % (user.pnick, p.pnick)
            )
            return 1
        if p.userlevel > user.userlevel:
            irc_msg.reply(
                "Unfortunately I like %s more than you. So none of that." % (p.pnick,)
            )
            return 1
        last_comp = self.was_recently_proposed("kick", p.id)
        prop_id = self.create_kick_proposal(user, p, comment, last_comp)
        reply = "%s created a new proposition (nr. %d) to kick %s." % (
            user.pnick,
            prop_id,
            p.pnick,
        )
        reply += (
            " When people have had a fair shot at voting you can call a count using !prop expire %d."
            % (prop_id,)
        )
        irc_msg.reply(reply)

    def process_poll_proposal(self, irc_msg, user, question, answers):
        if len(answers) > 1:
            prop_id = self.create_poll_proposal(user, question, answers)
            reply = "%s created a new poll (nr. %d)." % (
                user.pnick,
                prop_id,
            )
            reply += (
                " When people have been given a fair shot at voting you can call a count using !prop expire %d."
                % (prop_id,)
            )
        else:
            reply = "It's not much of a poll if it only has one answer, pal."
        irc_msg.reply(reply)

    def short_proposal_subject(self, person, question):
        subject = person
        if not subject:
            subject = question
            max_length = 40
            if len(subject) > max_length:
                subject = "%s..." % (subject[0:max_length-3],)
            subject = "%s?" %(subject,)
        return subject

    def process_list_all_proposals(self, irc_msg, user):
        u = loadable.user(pnick=irc_msg.user)
        u.load_from_db(self.cursor, irc_msg.round)
        query = "SELECT invite.id AS id, invite.person AS person, NULL AS question, 'invite' AS prop_type, created"
        query += " FROM invite_proposal AS invite"
        query += " WHERE invite.active"
        query += " UNION ("
        query += "     SELECT kick.id AS id, t3.pnick AS person, NULL AS question, 'kick' AS prop_type, created"
        query += "     FROM kick_proposal AS kick"
        query += "     INNER JOIN user_list AS t3 ON kick.person_id=t3.id"
        query += "     WHERE kick.active"
        query += " )"
        query += " UNION ("
        query += "     SELECT poll.id AS id, NULL AS person, poll.question AS question, 'poll' AS prop_type, created"
        query += "     FROM poll_proposal AS poll"
        query += "     WHERE poll.active"
        query += " ) ORDER BY created ASC"
        self.cursor.execute(query, ())
        a = []
        for r in self.cursor.fetchall():
            prop_info = "%s: %s %s" % (
                r["id"],
                r["prop_type"],
                self.short_proposal_subject(r["person"], r["question"]),
            )
            if not irc_msg.chan_reply():
                query = "SELECT t1.vote AS vote, t1.carebears AS carebears FROM prop_vote AS t1"
                query += " WHERE t1.prop_id=%s AND t1.voter_id=%s"
                self.cursor.execute(query, (r["id"], u.id))
                if self.cursor.rowcount > 0:
                    r = self.cursor.fetchone()
                    use_carebears = self.config.getboolean(
                        "Alliance", "use_carebears_for_props"
                    )
                    if use_carebears:
                        prop_info += " (%s,%s)" % (r["vote"][0].upper(), r["carebears"])
                    else:
                        prop_info += " (%s)" % (r["vote"][0].upper())
            a.append(prop_info)

        reply = "Propositions currently being voted on: %s" % (", ".join(a),)
        irc_msg.reply(reply)

    def process_show_proposal(self, irc_msg, u, prop_id):
        r = self.find_single_prop_by_id(prop_id)
        if not r:
            reply = "No proposition number %s exists." % (prop_id,)
            irc_msg.reply(reply)
            return

        age = (datetime.datetime.now() - r["created"]).days
        if r["prop_type"] == "poll":
            reply = (
                "proposition %s (%s %s old): poll. %s asked '%s?' and offered options"
                % (
                    r["id"],
                    age,
                    self.pluralize(age, "day"),
                    r["proposer"],
                    r["question"],
                )
            )
            query = "SELECT answer_index, answer_text"
            query += " FROM poll_answer"
            query += " WHERE poll_id=%s"
            self.cursor.execute(query, (prop_id,))
            answers = []
            for a in self.cursor.fetchall():
                answers.append(
                    '%s: "%s"' % (a["answer_index"].upper(), a["answer_text"])
                )
            reply += " %s" % ", ".join(answers)
        else:
            reply = "proposition %s (%s %s old): %s %s. %s commented '%s'" % (
                r["id"],
                age,
                self.pluralize(age, "day"),
                r["prop_type"],
                r["person"],
                r["proposer"],
                r["comment_text"],
            )
        if not bool(r["active"]):
            reply += ", this prop expired %d days ago." % (
                (datetime.datetime.now() - r["closed"]).days,
            )
        elif (
            irc_msg.target[0] != "#"
            or irc_msg.prefix_notice()
            or irc_msg.prefix_private()
        ):
            query = "SELECT vote,carebears FROM prop_vote"
            query += " WHERE prop_id=%s AND voter_id=%s"
            self.cursor.execute(query, (prop_id, u.id))
            s = self.cursor.fetchone()
            if s:
                vote = s["vote"][:1].upper() + s["vote"][1:]
                reply += ", you are currently voting '%s'" % (vote,)
                use_carebears = self.config.getboolean(
                    "Alliance", "use_carebears_for_props"
                )
                if use_carebears and s["vote"] != "abstain":
                    reply += " with %s carebears" % (s["carebears"],)
                reply += " on this proposition."
            else:
                reply += ", you are not currently voting on this proposition."

        outcome = self.get_voters_for_prop(prop_id, r["prop_type"])
        if len(outcome["veto"]["list"]) > 0:
            reply += " Vetoing: "
            reply += ", ".join([x["pnick"] for x in outcome["veto"]["list"]])
        irc_msg.reply(reply)

        if not bool(r["active"]):
            prop = self.find_single_prop_by_id(prop_id)

            if r["prop_type"] == "poll":
                reply = "The prop expired with %s winning" % (r["vote_result"])
                for o in sorted(outcome.keys()):
                    if o != "veto":
                        reply += ". The voters for %s were (%s)" % (
                            o,
                            self.pretty_print_votes(outcome[o]["list"]),
                        )
                reply += "."
            else:
                no = outcome["no"]["count"]
                yes = outcome["yes"]["count"]
                (
                    winners,
                    losers,
                    winning_total,
                    losing_total,
                ) = self.get_winners_and_losers(outcome)
                if r["vote_result"].upper() == "yes".upper():
                    reply = (
                        "The prop passed by a vote of %s carebears for and %s against"
                        % (yes, no)
                    )
                elif r["vote_result"].upper() == "no".upper():
                    reply = (
                        "The prop failed by a vote of %s carebears against and %s for"
                        % (no, yes)
                    )
                elif r["vote_result"].upper() == "cancel".upper():
                    reply = (
                        "The prop was cancelled with %s carebears for and %s against"
                        % (yes, no)
                    )
                reply += ". The voters in favor were ("
                reply += self.pretty_print_votes(outcome["yes"]["list"])
                reply += ") and against ("
                reply += self.pretty_print_votes(outcome["no"]["list"])
                reply += ")"
            irc_msg.reply(reply)

    def process_vote_proposal(self, irc_msg, u, prop_id, vote):
        use_carebears = self.config.getboolean("Alliance", "use_carebears_for_props")
        # Make sure we can distinguish between 'Someone voted with 1 bear' and
        # 'Someone voted but carebear weighing is disabled'.
        carebears = u.carebears if use_carebears else 0
        prop = self.find_single_prop_by_id(prop_id)
        if not prop:
            irc_msg.reply("No proposition number %s exists (idiot)." % (prop_id,))
            return

        if not bool(prop["active"]):
            irc_msg.reply("You can't vote on prop %s, it's expired." % (prop_id,))
            return
        if prop["proposer"].lower() == u.pnick.lower():
            reply = "Arbitrary Munin rule #167: No voting on your own props."
            irc_msg.reply(reply)
            return

        if (
            prop["person"]
            and prop["person"].lower() == u.pnick.lower()
            and vote == "veto"
        ):
            reply = "You can't veto a prop to kick you."
            irc_msg.reply(reply)
            return

        if prop["prop_type"] == "poll":
            query = """
            SELECT answer_index, answer_text
            FROM poll_answer
            WHERE poll_id = %s
            AND answer_index = %s
            """
            self.cursor.execute(query, (
                prop_id,
                vote.lower(),
            ))
            if self.cursor.rowcount == 0:
                query = """
                SELECT answer_index, answer_text
                FROM poll_answer
                WHERE poll_id = %s
                AND answer_text ILIKE %s
                """
                self.cursor.execute(query, (
                    prop_id,
                    "%" + vote + "%",
                ))
                if self.cursor.rowcount == 0:
                    irc_msg.reply("You can't vote '%s' on this poll, you moron" % (
                        vote,
                    ))
                    return 1
            if self.cursor.rowcount > 1:
                irc_msg.reply("Be more specific, I can't read your mind. Yet.")
                return 1
            else:
                row = self.cursor.fetchone()
                vote = row["answer_index"]
                vote_text = row["answer_text"]
        else:
            kick_inv_arr = ["yes", "no", "veto", "abstain"]
            # Many people add a comment when they vote on kick or invite props,
            # so we look only at the first word for those.
            vote = vote.split()[0]
            if vote.lower() not in kick_inv_arr:
                irc_msg.reply(
                    "You can only vote %s on a %s prop, you moron"
                    % (", ".join(kick_inv_arr), prop["prop_type"])
                )
                return

        allow_vetos = self.config.getboolean("Alliance", "allow_prop_veto")
        if not allow_vetos and vote.lower() == "veto":
            irc_msg.reply("No vetos today, buddy")
            return

        query = """
        SELECT v.id, v.vote, v.carebears, v.prop_id, a.answer_text
        FROM prop_vote AS v
        LEFT OUTER JOIN poll_answer AS a ON v.prop_id = a.poll_id AND v.vote = a.answer_index
        WHERE prop_id=%s
        AND voter_id=%s
        """
        self.cursor.execute(query, (
            prop_id,
            u.id,
        ))
        old_vote = self.cursor.fetchone()

        if old_vote:
            query = "DELETE FROM prop_vote WHERE id=%s AND voter_id=%s"
            self.cursor.execute(query, (old_vote["id"], u.id))

        query = "INSERT INTO prop_vote (vote,carebears,prop_id,voter_id) VALUES (%s,%s,%s,%s)"
        self.cursor.execute(query, (vote, carebears, prop["id"], u.id))
        if old_vote:
            reply = "Changed your vote on proposition %s from %s" % (
                prop["id"],
                old_vote["vote"],
            )
            if prop["prop_type"] == "poll":
                reply += " (%s)" % (
                    old_vote["answer_text"],
                )
            if use_carebears and old_vote["vote"] != "abstain":
                reply += " (%s)" % (old_vote["carebears"],)
            reply += " to %s" % (vote,)
            if prop["prop_type"] == "poll":
                reply += " (%s)" % (
                    vote_text,
                )
            if use_carebears and vote != "abstain":
                reply += " with %s carebears" % (carebears,)
            reply += "."
        else:
            reply = "Set your vote on proposition %s as %s" % (prop["id"], vote)
            if prop["prop_type"] == "poll":
                reply += " (%s)" % (vote_text,)
            if use_carebears and vote not in ["abstain", "veto"]:
                reply += " with %s carebears" % (carebears,)
            reply += "."
        irc_msg.reply(reply)

    def process_expire_proposal(self, irc_msg, u, prop_id):
        prop = self.find_single_prop_by_id(prop_id)
        if not prop:
            irc_msg.reply("No proposition number %s exists (idiot)." % (prop_id,))
            return
        if not prop["active"]:
            irc_msg.reply(
                "Only active props may be expired, prop %d has already expired"
                % (prop["id"],)
            )
            return
        if u.pnick.lower() != prop["proposer"].lower() and u.userlevel < 1000:
            irc_msg.reply(
                "Only %s may expire proposition %d." % (prop["proposer"], prop["id"])
            )
            return
        if prop["prop_type"] == "invite" and self.too_many_members(irc_msg):
            return
        # tally votes for and against
        outcome = self.get_voters_for_prop(prop_id, prop["prop_type"])
        highest = 0
        winner = None
        for o in sorted(outcome.keys()):
            if outcome[o]["count"] > highest and outcome[o]["count"] > 0:
                highest = outcome[o]["count"]
                winner = o

        age = (datetime.datetime.now() - prop["created"]).days
        if prop["prop_type"] == "poll":
            reply = "The poll raised by %s %s %s ago asking '%s?'" % (
                prop["proposer"],
                age,
                self.pluralize(age, "day"),
                prop["question"],
            )
            if not winner:
                reply += " has expired without any votes"
                winner = "abstain"
            elif winner == "veto":
                reply += " has expired with one or more vetoes"
            else:
                reply += " has expired with '%s!' as winner" % (outcome[winner]["text"])

            losing_total = 0
            for o in sorted(outcome.keys()):
                opt = o[:1].upper() + o[1:]
                text = outcome[o]["text"]
                if text:
                    reply += ". Voters for '%s': (%s)" % (
                        text,
                        self.pretty_print_votes(outcome[o]["list"]),
                    )
                else:
                    reply += ". Voters for %s: (%s)" % (
                        opt,
                        self.pretty_print_votes(outcome[o]["list"]),
                    )
            reply += "."

        else:
            (
                winners,
                losers,
                winning_total,
                losing_total,
            ) = self.get_winners_and_losers(outcome)

            reply = "The proposition raised by %s %s %s ago to %s has" % (
                prop["proposer"],
                age,
                self.pluralize(age, "day"),
                '%s %s' % (prop["prop_type"], prop["person"],) if prop["person"] else prop["prop_type"],
            )
            yes = outcome["yes"]["count"]
            no = outcome["no"]["count"]
            passed = yes > no and len(outcome["veto"]["list"]) <= 0
            if passed:
                reply += " passed"
                winner = "yes"
            else:
                reply += " failed"
                winner = "no"
            reply += " with %s carebears for and %s against." % (yes, no)
            reply += " In favor: ("
            reply += self.pretty_print_votes(outcome["yes"]["list"])
            reply += ") Against: ("
            reply += self.pretty_print_votes(outcome["no"]["list"])
            reply += ")"
            if len(outcome["veto"]["list"]) > 0:
                reply += " Veto: ("
                reply += self.pretty_print_votes(outcome["veto"]["list"])
                reply += ")"

        irc_msg.client.privmsg("#%s" % (self.config.get("Auth", "home"),), reply)

        if prop["prop_type"] == "kick" and passed:
            self.do_kick(irc_msg, prop, yes, no)
        elif prop["prop_type"] == "invite" and passed:
            self.do_invite(irc_msg, prop)

        query = "UPDATE %s_proposal SET active = FALSE, closed = NOW()" % (
            prop["prop_type"],
        )
        query += ", vote_result=%s,compensation=%s"
        query += " WHERE id=%s"
        self.cursor.execute(query, (winner, losing_total, prop["id"]))

    def process_cancel_proposal(self, irc_msg, u, prop_id):
        prop = self.find_single_prop_by_id(prop_id)
        if not prop:
            irc_msg.reply("No proposition number %s exists (idiot)." % (prop_id,))
            return

        if u.pnick.lower() != prop["proposer"].lower() and u.userlevel < 1000:
            irc_msg.reply(
                "Only %s may cancel proposition %d." % (prop["proposer"], prop["id"])
            )
            return

        if not prop["active"]:
            irc_msg.reply(
                "Only active props may be cancelled, prop %d has already expired"
                % (prop["id"],)
            )
            return

        outcome = self.get_voters_for_prop(prop_id, prop["prop_type"])

        query = "UPDATE %s_proposal SET active = FALSE, closed =NOW() " % (
            prop["prop_type"],
        )
        query += ", vote_result=%s"
        query += " WHERE id=%s"
        self.cursor.execute(query, ("cancel", prop["id"]))
        if prop["prop_type"] == "poll":
            reply = "Cancelled poll %s asking '%s?'" % (
                prop["id"],
                prop["question"],
            )
            for o in sorted(outcome.keys()):
                opt = o[:1].upper() + o[1:]
                text = outcome[o]["text"]
                if text:
                    reply += ". Voters for '%s!' (%s)" % (
                        text,
                        self.pretty_print_votes(outcome[o]["list"]),
                    )
                else:
                    reply += ". Voters for %s (%s)" % (
                        opt,
                        self.pretty_print_votes(outcome[o]["list"]),
                    )
            reply += "."
        else:
            reply = "Cancelled proposal %s to %s %s" % (
                prop["id"],
                prop["prop_type"],
                prop["person"],
            )
            reply += ". Voters in favor (%s)" % (
                self.pretty_print_votes(outcome["yes"]["list"])
            )
            reply += " and against (%s)" % (
                self.pretty_print_votes(outcome["no"]["list"])
            )

        irc_msg.client.privmsg("#%s" % (self.config.get("Auth", "home"),), reply)

    def process_recent_proposal(self, irc_msg, u):
        query = "SELECT inv.id AS id, inv.person AS person, NULL AS question, 'invite' AS prop_type, inv.vote_result AS vote_result, inv.closed AS closed"
        query += " FROM invite_proposal AS inv"
        query += " WHERE NOT inv.active"
        query += " UNION ("
        query += "     SELECT kick.id AS id, ulist.pnick AS person, NULL AS question, 'kick' AS prop_type, kick.vote_result AS vote_result, kick.closed AS closed"
        query += "     FROM kick_proposal AS kick"
        query += "     INNER JOIN user_list AS ulist ON kick.person_id=ulist.id"
        query += "     WHERE NOT kick.active"
        query += " )"
        query += " UNION ("
        query += "     SELECT poll.id AS id, NULL AS person, poll.question || '?' AS question, 'poll' AS prop_type, poll.vote_result AS vote_result, poll.closed AS closed"
        query += "     FROM poll_proposal AS poll"
        query += "     WHERE NOT poll.active"
        query += " )"
        query += " ORDER BY closed DESC LIMIT 30"
        self.cursor.execute(query, ())
        a = []
        for r in self.cursor.fetchall():
            a.append(
                "%s: %s %s %s"
                % (
                    r["id"],
                    r["prop_type"],
                    self.short_proposal_subject(r["person"], r["question"]),
                    r["vote_result"][0].upper() if r["vote_result"] else "",
                )
            )
        reply = "Recently expired propositions: %s" % (", ".join(a),)
        irc_msg.reply(reply)

    def process_search_proposal(self, irc_msg, u, search):
        query = "SELECT id, prop_type, person, question, vote_result FROM ("
        query += "     SELECT inv.id AS id, 'invite' AS prop_type, inv.person AS person, NULL as question, inv.vote_result AS vote_result"
        query += "     FROM invite_proposal AS inv"
        query += "     UNION ("
        query += "         SELECT kick.id AS id, 'kick' AS prop_type, ulist.pnick AS person, NULL as quesion, kick.vote_result AS vote_result"
        query += "         FROM kick_proposal AS kick INNER JOIN user_list AS ulist ON kick.person_id=ulist.id"
        query += "     )"
        query += "     UNION ("
        query += "         SELECT poll.id AS id, 'poll' AS prop_type, NULL AS person, poll.question AS question, poll.vote_result AS vote_result"
        query += "         FROM poll_proposal AS poll"
        query += "     )"
        query += " )"
        query += " AS prop"
        query += " WHERE prop.person ILIKE %s OR prop.question ILIKE %s"
        query += " ORDER BY id DESC"
        query += " LIMIT 10"
        self.cursor.execute(query, ("%" + search + "%", "%" + search + "%"))
        a = []
        for r in self.cursor.fetchall():
            a.append(
                "%s: %s %s %s"
                % (
                    r["id"],
                    r["prop_type"],
                    self.short_proposal_subject(r["person"], r["question"]),
                    r["vote_result"][0].upper() if r["vote_result"] else "",
                )
            )
        reply = "Propositions matching '%s': %s" % (
            search,
            ", ".join(a),
        )
        irc_msg.reply(reply)

    def get_winners_and_losers(self, outcome):
        if outcome["yes"]["count"] > outcome["no"]["count"]:
            losers = outcome["no"]["list"]
            losing_total = outcome["no"]["count"]
            winners = outcome["yes"]["list"]
            winning_total = outcome["yes"]["count"]
        else:
            winners = outcome["no"]["list"]
            winning_total = outcome["no"]["count"]
            losers = outcome["yes"]["list"]
            losing_total = outcome["yes"]["count"]
        return (winners, losers, winning_total, losing_total)

    def get_voters_for_prop(self, prop_id, prop_type):
        outcome = {}
        for a in ["veto"]:
            outcome[a] = {}
            outcome[a]["list"] = []
            outcome[a]["count"] = 0
            outcome[a]["text"] = ""

        if prop_type == "poll":
            query = "SELECT answer_index, answer_text"
            query += " FROM poll_answer"
            query += " WHERE poll_id=%s"
            self.cursor.execute(query, (prop_id,))
            for a in self.cursor.fetchall():
                index = a["answer_index"]
                outcome[index] = {}
                outcome[index]["list"] = []
                outcome[index]["count"] = 0
                outcome[index]["text"] = a["answer_text"]

        else:
            for a in ["yes", "no"]:
                outcome[a] = {}
                outcome[a]["list"] = []
                outcome[a]["count"] = 0
                outcome[a]["text"] = a

        query = "SELECT v.vote AS vote, v.carebears AS carebears, v.prop_id AS prop_id, v.voter_id AS voter_id, ulist.pnick AS pnick"
        query += " FROM prop_vote AS v"
        query += " INNER JOIN user_list AS ulist ON v.voter_id=ulist.id"
        query += " WHERE prop_id=%s"
        query += " AND NOT vote='abstain'"
        self.cursor.execute(query, (prop_id,))
        use_carebears = self.config.getboolean("Alliance", "use_carebears_for_props")
        for r in self.cursor.fetchall():
            vote = r["vote"]
            outcome[vote]["list"].append(r)
            outcome[vote]["count"] += r["carebears"] if use_carebears else 1

        return outcome

    def do_kick(self, irc_msg, prop, yes, no):
        idiot = self.load_user_from_pnick(prop["person"], irc_msg.round)
        home = self.config.get("Auth", "home")
        query = "UPDATE user_list SET userlevel = 1 WHERE id = %s"
        self.cursor.execute(query, (idiot.id,))
        irc_msg.client.privmsg(
            "Q",
            "removeuser #%s %s"
            % (
                home,
                idiot.pnick,
            ),
        )
        irc_msg.client.privmsg(
            "Q",
            "permban #%s *!*@%s.users.quakenet.org %s"
            % (home, idiot.pnick, prop["comment_text"]),
        )

        reply = "%s has been reduced to level 1 and removed from #%s." % (
            idiot.pnick,
            home,
        )
        irc_msg.client.privmsg("#%s" % (home), reply)

    def do_invite(self, irc_msg, prop):
        self.cursor.execute(
            "update user_list set alias_nick = NULL where alias_nick ilike %s",
            (prop["person"],)
        )
        gimp = self.load_user_from_pnick(prop["person"], irc_msg.round)
        home = self.config.get("Auth", "home")
        if not gimp or gimp.pnick.lower() != prop["person"].lower():
            query = "INSERT INTO user_list (userlevel,sponsor,pnick) VALUES (100,%s,%s)"
        else:
            query = (
                "UPDATE user_list SET userlevel = 100, sponsor=%s WHERE pnick ilike %s"
            )
        self.cursor.execute(query, (prop["proposer"], prop["person"]))
        irc_msg.client.privmsg(
            "Q",
            "adduser #%s %s"
            % (
                home,
                prop["person"],
            ),
        )
        irc_msg.client.privmsg(
            "Q",
            "chanlev #%s #%s +akot"
            % (
                home,
                prop["person"],
            ),
        )

        reply = "%s has been added to #%s and given level 100 access to me." % (
            prop["person"],
            home,
        )
        irc_msg.client.privmsg("#%s" % (home), reply)

    def find_single_prop_by_id(self, prop_id):
        query = "SELECT id, prop_type, proposer, person, created, padding, comment_text, active, closed, vote_result, question"
        query += " FROM ("
        query += "     SELECT inv.id AS id, 'invite' AS prop_type, ulist1.pnick AS proposer, inv.person AS person, inv.padding AS padding, inv.created AS created,"
        query += "            inv.comment_text AS comment_text, inv.active AS active, inv.closed AS closed, inv.vote_result, NULL AS question"
        query += "     FROM invite_proposal AS inv"
        query += "     INNER JOIN user_list AS ulist1 ON inv.proposer_id=ulist1.id"
        query += "     UNION ("
        query += "         SELECT kick.id AS id, 'kick' AS prop_type, ulist2.pnick AS proposer, ulist3.pnick AS person, kick.padding AS padding, kick.created AS created,"
        query += "                kick.comment_text AS comment_text, kick.active AS active, kick.closed AS closed, kick.vote_result, NULL AS question"
        query += "         FROM kick_proposal AS kick"
        query += "         INNER JOIN user_list AS ulist2 ON kick.proposer_id=ulist2.id"
        query += "         INNER JOIN user_list AS ulist3 ON kick.person_id=ulist3.id"
        query += "     )"
        query += "     UNION ("
        query += "         SELECT poll.id AS id, 'poll' AS prop_type, ulist4.pnick AS proposer, NULL AS person, poll.padding AS padding, poll.created AS created,"
        query += "                NULL AS comment_text, poll.active AS active, poll.closed AS closed, poll.vote_result, poll.question AS question"
        query += "         FROM poll_proposal AS poll"
        query += "         INNER JOIN user_list AS ulist4 ON poll.proposer_id=ulist4.id"
        query += "     )"
        query += " ) AS joined"
        query += " WHERE joined.id=%s"

        self.cursor.execute(query, (prop_id,))
        return self.cursor.fetchone()

    def is_member(self, person):
        query = "SELECT id FROM user_list WHERE pnick ilike %s AND userlevel >= 100"
        self.cursor.execute(query, (person,))
        return self.cursor.rowcount > 0

    def is_already_an_alias(self, person):
        query = "SELECT id FROM user_list WHERE alias_nick ilike %s AND userlevel >= 100"
        self.cursor.execute(query, (person,))
        return self.cursor.rowcount > 0

    def is_already_proposed_invite(self, person):
        query = "SELECT id FROM invite_proposal WHERE person ilike %s AND active"
        self.cursor.execute(query, (person,))
        return self.cursor.rowcount > 0

    def was_recently_proposed(self, prop_type, person_or_person_id):
        if prop_type == "kick":
            query = "SELECT vote_result,compensation FROM kick_proposal"
            query += " WHERE person_id = %s"
            query += " AND not active"
            query += " ORDER BY closed DESC"
        else:
            query = "SELECT vote_result,compensation FROM invite_proposal"
            query += " WHERE person ilike %s"
            query += " AND not active"
            query += " ORDER BY closed DESC"
        self.cursor.execute(query, (person_or_person_id,))
        r = self.cursor.fetchone()
        if r and r["vote_result"] != "yes":
            return r["compensation"]
        return 0

    def create_invite_proposal(self, user, person, comment, padding):
        query = (
            "INSERT INTO invite_proposal (proposer_id, person, comment_text, padding)"
        )
        query += " VALUES (%s, %s, %s, %s)"
        self.cursor.execute(query, (user.id, person, comment, padding))
        query = "SELECT id FROM invite_proposal WHERE proposer_id = %s AND person = %s AND active ORDER BY created DESC"
        self.cursor.execute(query, (user.id, person))
        return self.cursor.fetchone()["id"]

    def create_kick_proposal(self, user, person, comment, padding):
        query = (
            "INSERT INTO kick_proposal (proposer_id, person_id, comment_text, padding)"
        )
        query += " VALUES (%s, %s, %s, %s)"
        self.cursor.execute(query, (user.id, person.id, comment, padding))
        query = "SELECT id FROM kick_proposal WHERE proposer_id = %s AND person_id = %s AND active ORDER BY created DESC"
        self.cursor.execute(query, (user.id, person.id))
        return self.cursor.fetchone()["id"]

    def is_already_proposed_kick(self, person_id):
        query = "SELECT id FROM kick_proposal WHERE person_id = %s AND active"
        self.cursor.execute(query, (person_id,))
        return self.cursor.rowcount > 0

    def create_poll_proposal(self, user, question, answers):
        query = "INSERT INTO poll_proposal (proposer_id, question)"
        query += " VALUES (%s, %s)"
        self.cursor.execute(query, (user.id, question))

        query = "SELECT id FROM poll_proposal WHERE proposer_id = %s AND question = %s AND active ORDER BY created DESC LIMIT 1"
        self.cursor.execute(query, (user.id, question))
        poll_id = self.cursor.fetchone()["id"]

        # OPTIMIZE: Do this in 1 query.
        for i in range(0, len(answers)):
            query = "INSERT INTO poll_answer (poll_id, answer_index, answer_text)"
            query += " VALUES (%s, %s, %s)"
            self.cursor.execute(query, (poll_id, chr(ord("a") + i), answers[i]))

        return poll_id

    def pretty_print_votes(self, votes):
        use_carebears = self.config.getboolean("Alliance", "use_carebears_for_props")
        return ", ".join(
            [
                "%s (%s)"
                % (
                    v["pnick"],
                    v["carebears"],
                )
                if use_carebears
                else v["pnick"]
                for v in votes
            ]
        )
