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
import string
from munin import loadable
import datetime

class prop(loadable.loadable):
    """
    foo
    """
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(invite|kick|list|show|vote|expire|cancel|recent|search)(.*)")
        self.invite_kickre=re.compile(r"^\s+(\S+)(\s+(\S.*))")
        self.votere=re.compile(r"^\s+(\d+)\s+(yes|no|veto|abstain)")
        self.usage=self.__class__.__name__ + " [<invite|kick> <pnick> <comment>] | [list] | [vote <number> <yes|no|abstain>] | [expire <number>] | [show <number>] | [cancel <number>] | [recent] | [search <pnick>]"
        self.helptext=["A proposition is a vote to do something. For now, you can raise propositions to invite or kick someone. Once raised the proposition will stand until you expire it.  Make sure you give everyone time to have their say. Votes for and against a proposition are weighted by carebears. You must have at least 1 carebear to vote."]

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        u=self.load_user(user,irc_msg)
        if not u: return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0
        
        # assign param variables
        prop_type=m.group(1)

        if prop_type.lower() == 'invite':
            m=self.match_or_usage(irc_msg,self.invite_kickre,m.group(2))
            if not m: return 1
            if self.command_not_used_in_home(irc_msg,self.__class__.__name__ + " invite"): return 1
            if self.too_many_members(irc_msg): return 1
            person=m.group(1)
            comment=m.group(3)
            self.process_invite_proposal(irc_msg,u,person,comment)

        elif prop_type.lower() == 'kick':
            m=self.match_or_usage(irc_msg,self.invite_kickre,m.group(2))
            if not m: return 1
            if self.command_not_used_in_home(irc_msg,self.__class__.__name__ + " kick"): return 1

            person=m.group(1)
            comment=m.group(3)
            self.process_kick_proposal(irc_msg,u,person,comment)

        elif prop_type.lower() == 'list':
            self.process_list_all_proposals(irc_msg,u)

        elif prop_type.lower() == 'show':
            m=self.match_or_usage(irc_msg,re.compile(r"^\s*(\d+)"),m.group(2))
            if not m: return 1
            prop_id=int(m.group(1))
            self.process_show_proposal(irc_msg,u,prop_id)
            
        elif prop_type.lower() == 'vote':
            m=self.match_or_usage(irc_msg,self.votere,m.group(2))
            if not m: return 1
            prop_id=int(m.group(1))
            vote=m.group(2)
            self.process_vote_proposal(irc_msg,u,prop_id,vote)
           
        elif prop_type.lower() == 'expire':
            m=self.match_or_usage(irc_msg,re.compile(r"\s*(\d+)"),m.group(2))
            if not m: return 1
            if self.command_not_used_in_home(irc_msg,self.__class__.__name__ + " expire"): return 1
            prop_id=int(m.group(1))
            self.process_expire_proposal(irc_msg,u,prop_id)

        elif prop_type.lower() == 'cancel':
            m=self.match_or_usage(irc_msg,re.compile(r"\s*(\d+)"),m.group(2))
            if not m: return 1
            if self.command_not_used_in_home(irc_msg, self.__class__.__name__ + " cancel"): return 1
            prop_id=int(m.group(1))
            self.process_cancel_proposal(irc_msg, u, prop_id)
            
        elif prop_type.lower() == 'recent':
            self.process_recent_proposal(irc_msg,u)

        elif prop_type.lower() == 'search':
            m=self.match_or_usage(irc_msg,re.compile(r"\s*(\S+)"),m.group(2))
            if not m: return 1
            self.process_search_proposal(irc_msg,u,m.group(1))
        return 1

    def too_many_members(self,irc_msg):
        members=loadable.user.count_members(self.cursor)
        if members >= int(self.config.get('Alliance','member_limit')):
            irc_msg.reply("You have tried to invite somebody, but we have %s losers and I can't be bothered dealing with more than %s of you."%(members, self.config.get('Alliance','member_limit')))
            return 1
        return 0
            

    def process_invite_proposal(self,irc_msg,user,person,comment):
        if self.is_member(person):
            irc_msg.reply("Stupid %s, that wanker %s is already a member."%(user.pnick,person))
            return 1
        if self.is_already_proposed_invite(person):
            irc_msg.reply("Silly %s, there's already a proposal to invite %s."%(user.pnick,person))
            return 1
        last_comp=self.was_recently_proposed('invite',person)
        prop_id=self.create_invite_proposal(user,person,comment,last_comp)
        reply="%s created a new proposition (nr. %d) to invite %s." %(user.pnick,prop_id,person)
        reply+=" When people have been given a fair shot at voting you can call a count using !prop expire %d."%(prop_id,)
        irc_msg.reply(reply)

    def process_kick_proposal(self,irc_msg,user,person,comment):
        p=self.load_user_from_pnick(person)
        if person.lower() == "munin".lower():
            irc_msg.reply("I'll peck your eyes out, cunt.")
            return 1
        if not p or p.userlevel < 100:
            irc_msg.reply("Stupid %s, you can't kick %s, they're not a member."%(user.pnick,person))
            return 1
        if self.is_already_proposed_kick(p.id):
            irc_msg.reply("Silly %s, there's already a proposition to kick %s."%(user.pnick,p.pnick))
            return 1
        if p.userlevel > user.userlevel:
            irc_msg.reply("Unfortunately I like %s more than you. So none of that."%(p.pnick,))
            return 1
        last_comp=self.was_recently_proposed('kick',p.id)
        prop_id=self.create_kick_proposal(user,p,comment,last_comp)
        reply="%s created a new proposition (nr. %d) to kick %s."%(user.pnick,prop_id,p.pnick)
        reply+=" When people have had a fair shot at voting you can call a count using !prop expire %d."%(prop_id,)
        irc_msg.reply( reply)

    def process_list_all_proposals(self,irc_msg,user):
        query="SELECT t1.id AS id, t1.person AS person, 'invite' AS prop_type FROM invite_proposal AS t1 WHERE t1.active UNION ("
        query+=" SELECT t2.id AS id, t3.pnick AS person, 'kick' AS prop_type FROM kick_proposal AS t2"
        query+=" INNER JOIN user_list AS t3 ON t2.person_id=t3.id WHERE t2.active)"
        self.cursor.execute(query,())
        a=[]
        for r in self.cursor.dictfetchall():
            a.append("%s: %s %s"%(r['id'],r['prop_type'],r['person']))
        reply="Propositions currently being voted on: %s"%(string.join(a, ", "),)
        irc_msg.reply(reply)

    def process_show_proposal(self,irc_msg,u,prop_id):
        r=self.find_single_prop_by_id(prop_id)
        if not r:
            reply="No proposition number %s exists."%(prop_id,)
            irc_msg.reply(reply)
            return

        age=(datetime.datetime.now() - r['created']).days
        reply="proposition %s (%s %s old): %s %s. %s commented '%s'."%(r['id'],age,self.pluralize(age,"day"),
                                                                       r['prop_type'],r['person'],r['proposer'],
                                                                       r['comment_text'])
        if not bool(r['active']):
            reply+=" This prop expired %d days ago."%((datetime.datetime.now()-r['closed']).days,)
        if irc_msg.target[0] != "#" or irc_msg.prefix == irc_msg.client.NOTICE_PREFIX or irc_msg.prefix == irc_msg.client.PRIVATE_PREFIX:
            query="SELECT vote,carebears FROM prop_vote"
            query+=" WHERE prop_id=%s AND voter_id=%s"
            self.cursor.execute(query,(prop_id,u.id))
            s=self.cursor.dictfetchone()
            if s:
                reply+=" You are currently voting '%s'"%(s['vote'],)
                if s['vote'] != 'abstain':
                    reply+=" with %s carebears"%(s['carebears'],)
                reply+=" on this proposition."
            else:
                reply+=" You are not currently voting on this proposition."

        (voters, yes, no) = self.get_voters_for_prop(prop_id)
        if len(voters['veto']) > 0:
            reply+=" Vetoing: "
            reply+=string.join(map(lambda x:x['pnick'],voters['veto']),', ')
        irc_msg.reply(reply)
        

        if not bool(r['active']):
            reply=""
            prop=self.find_single_prop_by_id(prop_id)
            (winners,losers,winning_total,losing_total)=self.get_winners_and_losers(voters,yes,no)
            reply+="The prop"
            if yes > no:
                reply+=" passed by a vote of %s to %s"%(yes,no)
            else:
                reply+=" failed by a vote of %s to %s"%(no,yes)
            reply+=". The voters in favor were ("
            pretty_print=lambda x:"%s (%s)"%(x['pnick'],x['carebears'])
            reply+=string.join(map(pretty_print,voters['yes']),', ')
            reply+=") and against ("
            reply+=string.join(map(pretty_print,voters['no']),', ')
            reply+=")"
            irc_msg.reply(reply)

    def process_vote_proposal(self,irc_msg,u,prop_id,vote):
        # todo ensure prop is active
        carebears=u.carebears
        prop=self.find_single_prop_by_id(prop_id)
        if not prop:
            irc_msg.reply("No proposition number %s exists (idiot)."%(prop_id,))
            return

        if not bool(prop['active']):
            irc_msg.reply("You can't vote on prop %s, it's expired."%(prop_id,))
            return
        if prop['proposer'].lower() == u.pnick.lower():
            reply="Arbitrary Munin rule #167: No voting on your own props."
            irc_msg.reply(reply)
            return

        if prop['person'].lower() == u.pnick.lower() and vote == 'veto':
            reply="You can't veto a vote to kick you."
            irc_msg.reply(reply)
            return

        query="SELECT id,vote,carebears, prop_id FROM prop_vote"
        query+=" WHERE prop_id=%s AND voter_id=%s"
        self.cursor.execute(query,(prop_id,u.id))
        old_vote=self.cursor.dictfetchone()

        if old_vote:
            query="DELETE FROM prop_vote WHERE id=%s AND voter_id=%s"
            self.cursor.execute(query,(old_vote['id'],u.id))

        query="INSERT INTO prop_vote (vote,carebears,prop_id,voter_id) VALUES (%s,%s,%s,%s)"
        self.cursor.execute(query,(vote,carebears,prop['id'],u.id))
        if old_vote:
            reply="Changed your vote on proposition %s from %s"%(prop['id'],old_vote['vote'])
            if old_vote['vote'] != 'abstain':
                reply+=" (%s)"%(old_vote['carebears'],)
            reply+=" to %s"%(vote,)
            if vote != 'abstain':
                reply+=" with %s carebears"%(carebears,)
            reply+="."
        else:
            reply="Set your vote on proposition %s as %s"%(prop['id'],vote)
            if vote != 'abstain' and vote != 'veto':
                reply+=" with %s carebears"%(carebears,)
            reply+="."
        irc_msg.reply(reply)

    def process_expire_proposal(self,irc_msg,u,prop_id):
        prop=self.find_single_prop_by_id(prop_id)
        if not prop:
            irc_msg.reply("No proposition number %s exists (idiot)."%(prop_id,))
            return
        if u.pnick.lower() != prop['proposer'].lower() and u.userlevel < 1000:
            irc_msg.reply("Only %s may expire proposition %d."%(prop['proposer'],prop['id']))
            return
        #tally votes for and against
        (voters, yes, no) = self.get_voters_for_prop(prop_id)
        (winners,losers,winning_total,losing_total)=self.get_winners_and_losers(voters,yes,no)

        age=(datetime.datetime.now()-prop['created']).days
        reply="The proposition raised by %s %s %s ago to %s %s has"%(prop['proposer'],age,self.pluralize(age,"day"),prop['prop_type'],prop['person'])
        passed = yes > no and len(voters['veto']) <= 0
        if passed:
            reply+=" passed"
        else:
            reply+=" failed"
        reply+=" with %s carebears for and %s against."%(yes,no)
        reply+=" In favor: "

        pretty_print=lambda x:"%s (%s)"%(x['pnick'],x['carebears'])
        reply+=string.join(map(pretty_print,voters['yes']),', ')
        reply+=" Against: "
        reply+=string.join(map(pretty_print,voters['no']),', ')
        if len(voters['veto']) > 0:
            reply+=" Veto: "
            reply+=string.join(map(pretty_print,voters['veto']),', ')
            
        irc_msg.client.privmsg("#%s"%(self.config.get('Auth','home'),),reply)

        if prop['prop_type'] == 'kick' and passed:
            self.do_kick(irc_msg,prop,yes,no)
        elif prop['prop_type'] == 'invite' and passed:
            self.do_invite(irc_msg,prop)

        query="UPDATE %s_proposal SET active = FALSE, closed = NOW()" % (prop['prop_type'],)
        query+=", vote_result=%s,compensation=%s"
        query+=" WHERE id=%s"
        self.cursor.execute(query,(['no','yes'][passed],losing_total,prop['id']))

    def process_cancel_proposal(self, irc_msg, u, prop_id):
        prop=self.find_single_prop_by_id(prop_id)
        if not prop:
            irc_msg.reply("No proposition number %s exists (idiot)."%(prop_id,))
            return

        if u.pnick.lower() != prop['proposer'].lower() and u.userlevel < 1000:
            irc_msg.reply("Only %s may expire proposition %d."%(prop['proposer'],prop['id']))
            return

        if not prop['active']:
            irc_msg.reply("Only active props may be cancelled, prop %d has already expired"%(prop['id'],))
            return


        (voters, yes, no)=self.get_voters_for_prop(prop_id)
        query="DELETE FROM prop_vote WHERE prop_id=%s"
        self.cursor.execute(query,(prop['id'],))

        query="DELETE FROM %s_proposal " %(prop['prop_type'],)
        query+=" WHERE id=%s"
        self.cursor.execute(query,(prop['id'],))

        reply="Cancelled proposal %s to %s %s. Voters in favor (" %(prop['id'],prop['prop_type'],prop['person'])

        pretty_print=lambda x:"%s (%s)"%(x['pnick'],x['carebears'])
        reply+=string.join(map(pretty_print,voters['yes']),', ')
        reply+=") and against ("
        reply+=string.join(map(pretty_print,voters['no']),', ')
        reply+=")"
        irc_msg.client.privmsg("#%s"%(self.config.get('Auth','home'),),reply)

    def process_recent_proposal(self,irc_msg,u):
        query="SELECT t1.id AS id, t1.person AS person, 'invite' AS prop_type, t1.vote_result AS vote_result FROM invite_proposal AS t1 WHERE NOT t1.active UNION ("
        query+=" SELECT t2.id AS id, t3.pnick AS person, 'kick' AS prop_type, t2.vote_result AS vote_result FROM kick_proposal AS t2"
        query+=" INNER JOIN user_list AS t3 ON t2.person_id=t3.id WHERE NOT t2.active) ORDER BY id DESC LIMIT 10"
        self.cursor.execute(query,())
        a=[]
        for r in self.cursor.dictfetchall():
            a.append("%s: %s %s %s"%(r['id'],r['prop_type'],r['person'],r['vote_result'][0].upper() if r['vote_result'] else ""))
        reply="Recently expired propositions: %s"%(string.join(a, ", "),)
        irc_msg.reply(reply)

    def process_search_proposal(self,irc_msg,u,search):
        query="SELECT id, prop_type, person, vote_result FROM ("
        query+=" SELECT t1.id AS id, 'invite' AS prop_type, t1.person AS person, t1.vote_result AS vote_result"
        query+="  FROM invite_proposal AS t1 UNION ("
        query+=" SELECT t3.id AS id, 'kick' AS prop_type, t5.pnick AS person, t3.vote_result AS vote_result"
        query+="  FROM kick_proposal AS t3 INNER JOIN user_list AS t5 ON t3.person_id=t5.id)) "
        query+="AS t6 WHERE t6.person ILIKE %s ORDER BY id DESC LIMIT 10"
        self.cursor.execute(query,("%"+search+"%",))
        a=[]
        for r in self.cursor.dictfetchall():
            a.append("%s: %s %s %s"%(r['id'],r['prop_type'],r['person'],r['vote_result'][0].upper() if r['vote_result'] else "",))
        reply="Propositions matching '%s': %s"%(search,string.join(a, ", "),)
        irc_msg.reply(reply)

    def get_winners_and_losers(self,voters,yes,no):
        if yes > no:
            losers=voters['no']
            winners=voters['yes']
            winning_total=yes
            losing_total=no
        else:
            winners=voters['no']
            losers=voters['yes']
            winning_total=no
            losing_total=yes
        return (winners,losers,winning_total,losing_total)

    def get_voters_for_prop(self,prop_id):
        query="SELECT t1.vote AS vote,t1.carebears AS carebears"
        query+=", t1.prop_id AS prop_idd,t1.voter_id AS voter_id,t2.pnick AS pnick"
        query+=" FROM prop_vote AS t1"
        query+=" INNER JOIN user_list AS t2 ON t1.voter_id=t2.id"
        query+=" WHERE prop_id=%s"
        self.cursor.execute(query,(prop_id,))
        voters={}
        voters['yes']=[]
        voters['no']=[]
        voters['abstain']=[]
        voters['veto']=[]
        yes=0;no=0

        for r in self.cursor.dictfetchall():
            if r['vote'] == 'yes':
                yes+=r['carebears']
                voters['yes'].append(r)
            elif r['vote'] == 'no':
                no+=r['carebears']
                voters['no'].append(r)
            elif r['vote'] == 'abstain':
                voters['abstain'].append(r)
            elif r['vote'] == 'veto':
                voters['veto'].append(r)
        return (voters, yes, no)

    def do_kick(self,irc_msg,prop,yes,no):
        idiot=self.load_user_from_pnick(prop['person'])
        query="UPDATE user_list SET userlevel = 1 WHERE id = %s"
        self.cursor.execute(query,(idiot.id,))
        irc_msg.client.privmsg('p','remuser #%s %s'%(self.config.get('Auth', 'home'), idiot.pnick,))
        irc_msg.client.privmsg('p',"ban #%s *!*@%s.users.netgamers.org %s"%(self.config.get('Auth', 'home'), idiot.pnick,prop['comment_text']))

        irc_msg.client.privmsg('p',"note send %s A proposition to kick you from %s has been raised by %s with reason '%s' and passed by a vote of %s to %s."%(idiot.pnick,self.config.get('Auth','alliance'),prop['proposer'],prop['comment_text'],yes,no))

        reply="%s has been reduced to level 1 and removed from #%s."%(idiot.pnick,self.config.get('Auth','home'))
        irc_msg.client.privmsg('#%s'%(self.config.get('Auth','home')),reply)

    def do_invite(self,irc_msg,prop):
        gimp=self.load_user_from_pnick(prop['person'])
        if not gimp or gimp.pnick.lower() != prop['person'].lower():
            query="INSERT INTO user_list (userlevel,sponsor,pnick) VALUES (100,%s,%s)"
        else:
            query="UPDATE user_list SET userlevel = 100, sponsor=%s WHERE pnick ilike %s"
        self.cursor.execute(query,(prop['proposer'],prop['person']))
        irc_msg.client.privmsg('P',"adduser #%s %s 399" %(self.config.get('Auth', 'home'), prop['person'],));
        irc_msg.client.privmsg('P',"modinfo #%s automode %s op" %(self.config.get('Auth', 'home'), prop['person'],));

        reply="%s has been added to #%s and given level 100 access to me."%(prop['person'],self.config.get('Auth','home'))
        irc_msg.client.privmsg('#%s'%(self.config.get('Auth','home')),reply)

    def find_single_prop_by_id(self,prop_id):
        query="SELECT id, prop_type, proposer, person, created, padding, comment_text, active, closed FROM ("
        query+="SELECT t1.id AS id, 'invite' AS prop_type, t2.pnick AS proposer, t1.person AS person, t1.padding AS padding, t1.created AS created,"
        query+=" t1.comment_text AS comment_text, t1.active AS active, t1.closed AS closed"
        query+=" FROM invite_proposal AS t1 INNER JOIN user_list AS t2 ON t1.proposer_id=t2.id UNION ("
        query+=" SELECT t3.id AS id, 'kick' AS prop_type, t4.pnick AS proposer, t5.pnick AS person, t3.padding AS padding, t3.created AS created,"
        query+=" t3.comment_text AS comment_text, t3.active AS active, t3.closed AS closed"
        query+=" FROM kick_proposal AS t3"
        query+=" INNER JOIN user_list AS t4 ON t3.proposer_id=t4.id"
        query+=" INNER JOIN user_list AS t5 ON t3.person_id=t5.id)) AS t6 WHERE t6.id=%s"
        
        self.cursor.execute(query,(prop_id,))
        return self.cursor.dictfetchone()

    def is_member(self,person):
        query="SELECT id FROM user_list WHERE pnick ilike %s AND userlevel >= 100"
        self.cursor.execute(query,(person,))
        return self.cursor.rowcount > 0

    def is_already_proposed_invite(self,person):
        query="SELECT id FROM invite_proposal WHERE person ilike %s AND active"
        self.cursor.execute(query,(person,))
        return self.cursor.rowcount > 0

    def was_recently_proposed(self,prop_type,person_or_person_id):
        query="SELECT vote_result,compensation FROM %s_proposal WHERE person%s"%(prop_type,['','_id'][prop_type=='kick'])
        query+=" ilike %s AND not active ORDER BY closed DESC"
        self.cursor.execute(query,(person_or_person_id,))
        r=self.cursor.dictfetchone()
        if r and r['vote_result'] != 'yes':
            return r['compensation']
        return 0
    
    def create_invite_proposal(self,user,person,comment,padding):
        query="INSERT INTO invite_proposal (proposer_id, person, comment_text, padding)"
        query+=" VALUES (%s, %s, %s, %s)"
        self.cursor.execute(query,(user.id,person,comment,padding))
        query="SELECT id FROM invite_proposal WHERE proposer_id = %s AND person = %s AND active ORDER BY created DESC"
        self.cursor.execute(query,(user.id,person))
        return self.cursor.dictfetchone()['id']

    def create_kick_proposal(self,user,person,comment,padding):
        query="INSERT INTO kick_proposal (proposer_id, person_id, comment_text, padding)"
        query+=" VALUES (%s, %s, %s, %s)"
        self.cursor.execute(query,(user.id,person.id,comment,padding))
        query="SELECT id FROM kick_proposal WHERE proposer_id = %s AND person_id = %s AND active ORDER BY created DESC"
        self.cursor.execute(query,(user.id,person.id))
        return self.cursor.dictfetchone()['id']

    def is_already_proposed_kick(self,person_id):
        query="SELECT id FROM kick_proposal WHERE person_id = %s AND active" 
        self.cursor.execute(query,(person_id,))
        return self.cursor.rowcount > 0

