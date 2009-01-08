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



class prop(loadable.loadable):
    """ 
    foo 
    """ 
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,100)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(invite|kick|list|show|vote)(.*)")
        self.invite_kickre=re.compile(r"^\s+(\S+)(\s+(\S.*))")
        self.votere=re.compile(r"^\s+(\d+)\s+(yes|no|abstain)(\s+(\d+))?")
        self.usage=self.__class__.__name__ + " [<invite|kick> <pnick> <comment>] | [<list>] | [<vote> <number> <yes|no|abstain> [carebears]] | [<expire> <number] | [<show> <number>]"
	self.helptext=["A proposition is a vote to do something. For now, you can raise propositions to invite or kick someone. Once raised the proposition will stand until you expire it.  Make sure you give everyone time to have their say.",
                       "Votes for and against a proposition are made using carebears. You must have at least 1 carebear to vote. You can bid as many carebears as you want, and if you lose, you'll be compensated this many carebears for being outvoted. If you win, you'll get some back, but I'll take enough to compensate the losers."]

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        u=self.load_user(user,prefix,nick,target)
        if not u: return 0
        
        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0
        
        # assign param variables 
        prop_type=m.group(1)

        if prop_type.lower() == 'invite':
            m=self.match_or_usage(prefix,nick,target,self.invite_kickre,m.group(2))
            if not m: return 1
            person=m.group(1)
            comment=m.group(3)
            self.process_invite_proposal(prefix,nick,target,u,person,comment)
            
        elif prop_type.lower() == 'kick':
            m=self.match_or_usage(prefix,nick,target,self.invite_kickre,m.group(2))
            if not m: return 1
            person=m.group(1)
            comment=m.group(3)
            self.process_kick_proposal(prefix,nick,target,u,person,comment)
            
        elif prop_type.lower() == 'list':
            self.process_list_all_proposals(prefix,nick,target,u)

        elif prop_type.lower() == 'show':
            m=self.match_or_usage(prefix,nick,target,re.compile(r"^\s*(\d+)"),m.group(2))
            if not m: return 1
            prop_id=int(m.group(1))
            self.process_show_proposal(prefix,nick,target,prop_id)
        elif prop_type.lower() == 'vote':
            m=self.match_or_usage(prefix,nick,target,self.votere,m.group(2))
            if not m: return 1
            prop_id=int(m.group(1))
            vote=m.group(2)
            carebears=m.group(3)
            if carebears: carebears=int(carebears)
            self.process_vote_proposal(prefix,nick,target,u,prop_id,vote,carebears)
        # Do stuff here

        return 1
    
    def process_invite_proposal(self,prefix,nick,target,user,person,comment):
        if self.is_member(person):
            self.client.reply(prefix,nick,target,"Stupid %s, that wanker %s is already a member."%(user.pnick,person))
            return 1
        if self.is_already_proposed_invite(person):
            self.client.reply(prefix,nick,target,"Silly %s, there's already a proposal to invite %s (I'm voting against)."%(user.pnick,person))
            return 1
        prop_id=self.create_invite_proposal(user,person,comment)
        reply="%s created a new proposition (nr. %d) to invite %s." %(user.pnick,prop_id,person)
        reply+=" When people have been given a fair shot at voting you can call a count using !expire %d and it'll tell everyone whether you got what you wanted or got rich."%(prop_id,)
        self.client.reply(prefix,nick,target,reply)

    def process_kick_proposal(self,prefix,nick,target,user,person,comment):
        p=self.load_user_from_pnick(person)
        if not p:
            self.client.reply(prefix,nick,target,"Stupid %s, you can't kick %s, they're not a member.")
            return 1
        if self.is_already_proposed_kick(p.id):
            self.client.reply(prefix,nick,target,"Silly %s, there's already a proposition to kick %s (I'm voting against)."%(user.pnick,p.pnick))
            return 1
        prop_id=self.create_kick_proposal(user,p,comment)
        reply="%s created a new proposition (nr. %d) to kick %s."%(user.pnick,prop_id,p.pnick)
        reply+=" When people have had a fair shot at voting you can call a count using !expire %d and it'll tell everyone whether %s is out or you're rich."%(prop_id,p.pnick)
        self.client.reply(prefix,nick,target, reply)

    def process_list_all_proposals(self,prefix,nick,target,user):
        query="SELECT t1.id AS id, t1.person AS person, 'invite' AS prop_type FROM invite_proposal AS t1 WHERE t1.active UNION ("
        query+=" SELECT t2.id AS id, t3.pnick AS person, 'kick' AS prop_type FROM kick_proposal AS t2"
        query+=" INNER JOIN user_list AS t3 ON t2.person_id=t3.id WHERE t2.active)"
        self.cursor.execute(query,())
        a=[]
        for r in self.cursor.dictfetchall():
            a.append("%d: %s %s"%(r['id'],r['prop_type'],r['person']))
        reply="Propositions currently being voted on: %s"%(string.join(a, ", "),)
        self.client.reply(prefix,nick,target,reply)

    def process_show_proposal(self,prefix,nick,target,prop_id):
        r=self.find_single_prop_by_id(prop_id)
        if not r:
            reply="No proposition number %d exists."%(prop_id,)
        else:
        
            age=DateTime.Age(DateTime.now(),r['created']).days
            reply="proposition %d (%d %s old): %s %s. %s says %s."%(r['id'],age,self.pluralize(age,"day"),
                                                                  r['prop_type'],r['person'],r['proposer'],
                                                                  r['comment_text'])
            if target[0] != "#" or prefix == self.client.NOTICE_PREFIX or prefix == self.client.PRIVATE_PREFIX:
                query="SELECT vote,carebears FROM prop_vote"
                query+=" WHERE prop_id=%d"
                self.cursor.execute(query,(prop_id,))
                s=self.cursor.dictfetchone()
                if s:
                    reply+=" You are currently voting '%s'"%(s['vote'],)
                    if s['vote'] != 'abstain':
                        reply+=" with %d carebears"%(s['carebears'],)
                    reply+=" on this proposition." 
                else:
                    reply+=" You are not currently voting on this proposition."
        self.client.reply(prefix,nick,target,reply)

    def process_vote_proposal(self,prefix,nick,target,u,prop_id,vote,carebears):
        # todo ensure prop is active
        if not carebears:
            if vote == 'abstain':
                carebears=0
            else:
                carebears=1
        prop=self.find_single_prop_by_id(prop_id)
        if not prop:
            self.client.reply(prefix,nick,target,"No proposition number %d exists (idiot)."%(prop_id,))
            return
        query="SELECT id,vote,carebears, prop_id FROM prop_vote"
        query+=" WHERE prop_id=%d"
        self.cursor.execute(query,(prop_id,))
        old_vote=self.cursor.dictfetchone()
        cost=0
        if old_vote:
            cost=carebears-old_vote['carebears']
        else:
            cost=carebears

        if cost > u.carebears:
            self.client.reply(prefix,nick,target,"You don't have enough carebears to cover that vote. Your vote would have required %d, but you only have %d carebears."%(cost,u.carebears))
            return
        #deduct carebears
        query="UPDATE user_list SET carebears = carebears - %d WHERE id = %d"
        self.cursor.execute(query,(cost,u.id))
        if old_vote:
            query="DELETE FROM prop_vote WHERE id=%d"
            self.cursor.execute(query,(old_vote['id'],))

        query="INSERT INTO prop_vote (vote,carebears,prop_id) VALUES (%s,%d,%d)"
        self.cursor.execute(query,(vote,carebears,prop['id']))
        if old_vote:
            reply="Changed your vote on proposition %d from %s"%(prop['id'],old_vote['vote'])
            if old_vote['vote'] != 'abstain':
                reply+=" (%d)"%(old_vote['carebears'],)
            reply+=" to %s"%(vote,)
            if vote != 'abstain':
                reply+=" with %d carebears"%(carebears,)
            reply+="."
        else:
            reply="Set your vote on proposition %d as %s"%(prop['id'],vote)
            if vote != 'abstain':
                reply+="with %d carebears."%(carebears,)
            reply+="."
        self.client.reply(prefix,nick,target,reply)

    def find_single_prop_by_id(self,prop_id):
        query="SELECT id, prop_type, proposer, person, created, comment_text FROM ("
        query+="SELECT t1.id AS id, 'invite' AS prop_type, t2.pnick AS proposer, t1.person AS person, t1.created AS created, t1.comment_text AS comment_text"
        query+=" FROM invite_proposal AS t1 INNER JOIN user_list AS t2 ON t1.proposer_id=t2.id UNION ("
        query+=" SELECT t3.id AS id, 'kick' AS prop_type, t4.pnick AS proposer, t5.pnick AS person, t3.created AS created, t3.comment_text AS comment_text"
        query+=" FROM kick_proposal AS t3"
        query+=" INNER JOIN user_list AS t4 ON t3.proposer_id=t4.id"
        query+=" INNER JOIN user_list AS t5 ON t3.person_id=t5.id)) AS t6 WHERE t6.id=%d"
        
        self.cursor.execute(query,(prop_id,))
        return self.cursor.dictfetchone()
    def is_member(self,person):
        query="SELECT id FROM user_list WHERE pnick ilike %s AND userlevel >= 100"
        self.cursor.execute(query,(person,))
        return self.cursor.rowcount > 0 

    def is_already_proposed_invite(self,person):
        query="SELECT id FROM invite_proposal WHERE person ilike %s"
        self.cursor.execute(query,(person,))
        return self.cursor.rowcount > 0 
    
    def create_invite_proposal(self,user,person,comment):
        query="INSERT INTO invite_proposal (proposer_id, person, comment_text)"
        query+=" VALUES (%s, %s, %s)"
        self.cursor.execute(query,(user.id,person,comment))
        query="SELECT id FROM invite_proposal WHERE proposer_id = %d AND person = %s AND active ORDER BY created DESC"
        self.cursor.execute(query,(user.id,person))
        return self.cursor.dictfetchone()['id']

    def create_kick_proposal(self,user,person,comment):
        query="INSERT INTO kick_proposal (proposer_id, person_id, comment_text)"
        query+=" VALUES (%s, %s, %s)"
        self.cursor.execute(query,(user.id,person.id,comment))
        query="SELECT id FROM kick_proposal WHERE proposer_id = %d AND person_id = %d AND active ORDER BY created DESC"
        self.cursor.execute(query,(user.id,person.id))
        return self.cursor.dictfetchone()['id']
        
    def is_already_proposed_kick(self,person_id):
        query="SELECT id FROM kick_proposal WHERE person_id = %d"
        self.cursor.execute(query,(person_id,))
        return self.cursor.rowcount > 0
