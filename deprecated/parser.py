"""
Parser class
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

import irc_message
import re
import psycopg
import sys
#sys.path.insert(0, "custom")
import os
import traceback
import string
import math
import loadable
from custom import scan
from custom import galstatus
import datetime
import md5
from mx import DateTime
from clickatell import Clickatell


DEBUG = 1

# This is such a beast...

class parser:
    def __init__(self, config, client, munin):
        # Private variables
        self.notprefix=r"~|-|\."
        self.pubprefix=r"!"
        self.privprefix='@'
        self.client=client
        self.munin=munin
        self.ctrl_list={}
        self.config = config

        #database variables (also private)
        self.mod_dir="mod"
        self.user=config.get("Database", "user")
        self.dbname=config.get("Database", "dbname")
        self.dsn = 'user=%s dbname=%s' % (self.user, self.dbname)
        if config.has_option("Database", "password"):
            self.dsn += ' password=%s' % config.get("Database", "password")
        if config.has_option("Database", "host"):
            self.dsn += ' host=%s' % config.get("Database", "host")
        # database connection and cursor
        self.conn=psycopg.connect(self.dsn)
        self.conn.serialize()
        self.conn.autocommit()
        self.cursor=self.conn.cursor()

        self.galstatus=galstatus.galstatus(self.client,self.conn,self.cursor,config)

        # Necessary regexps (still private)
        self.welcomre=re.compile(r"\S+\s+001.*",re.I)

        # obey P
        self.pinvitere=re.compile(r"^:P!cservice@netgamers.org\s+INVITE\s+\S+\s+:#(\S+)",re.I)

        # privmsg command regexes
        self.privmsgre=re.compile(r"^:(\S+)!(\S+)@(\S+)\s+PRIVMSG\s+(\S+)\s+:(.*)")

        self.ischannelre=re.compile(r"(#\S+)")

        self.pnickre=re.compile(r"(\S{2,15})\.users\.netgamers\.org")

        self.reg_controllers()

        self.commandre=re.compile(r"^(%s|%s|%s)(.*)\s*$" % (self.notprefix,self.pubprefix,self.privprefix))
        self.loadmodre=re.compile(r"^loadmod\s+(\S+)")
        self.helpre=re.compile(r"^help(\s+(\S+))?")

        self.scanre=re.compile("http://[^/]+/showscan.pl\?scan_id=([0-9a-zA-Z]+)")
        self.scangrpre=re.compile("http://[^/]+/showscan.pl\?scan_grp=([0-9a-zA-Z]+)")
    def parse(self,line):
        i=irc_message.irc_message()
        m=self.welcomre.search(line)
        if m:
            if self.config.has_option("IRC","auth"): self.client.wline("PRIVMSG P@cservice.netgamers.org :auth %s" % (self.config.get("IRC", "auth")))
            if self.config.has_option("IRC", "modes"): self.client.wline("MODE %s +%s" % (self.munin.nick, self.config.get("IRC", "modes")))
            return None
        m=self.pinvitere.search(line)
        if m:
            self.client.wline("JOIN #%s" % m.group(1))
            return None
        m=self.privmsgre.search(line);
        if m:
            nick=m.group(1).lower()
            username=m.group(2).lower()
            host=m.group(3).lower()
            target=m.group(4).lower()
            message=m.group(5)

            user=self.getpnick(host)

            #print "running scan parse"
            for m in self.scanre.finditer(message):
                self.scan(m.group(1),nick,user,None)
                pass
            for m in self.scangrpre.finditer(message):
                self.scan(None, nick, user, m.group(1))
                pass
            self.galstatus.parse(message,nick,user,target)

            m=self.commandre.search(message)
            if not m:
                return None
            prefix=m.group(1)
            command=m.group(2)


            query="SELECT * FROM access_level(%s,%s,%d)"
            self.cursor.execute(query,(user,target,self.prefix_to_numeric(prefix) == self.client.NOTICE_PREFIX or self.prefix_to_numeric(prefix) == self.client.PRIVATE_PREFIX))
            access=self.cursor.dictfetchone()['access_level'] or 0
            print "access: %d, user: %s, #channel: %s"%(access,user,target)

            com_list = command.split(' ',1)

            if command.lower() != 'pref' and len(com_list) > 0:
                query="INSERT INTO command_log (command_prefix,command,command_parameters,nick,pnick,username,hostname,target)"
                query+=" VALUES"
                query+=" (%s,%s,%s,%s,%s,%s,%s,%s)"

                command_command = com_list[0]
                command_parameters = None
                if len(com_list) > 1:
                    command_parameters = com_list[1]
                try:
                    self.cursor.execute(query,(prefix,command_command,command_parameters,nick,user,username,host,target))
                except Exception, e:
                    print "Exception during command logger: " + e.__str__()


            if access >= 0:
                m=self.loadmodre.search(command)
                if m:
                    if access < 1000:
                        self.client.reply(self.prefix_to_numeric(prefix),nick,target,"Fuck off twat")
                        return None
                    mod_name=m.group(1)
                    err_msg=self.load_mod(mod_name)
                    if err_msg:
                        self.client.reply(self.prefix_to_numeric(prefix),nick,target,"Failed to load module '%s' with reason: '%s'" % (mod_name,err_msg))
                    else:
                        self.client.reply(self.prefix_to_numeric(prefix),nick,target,"Successfully loaded module '%s'" % (mod_name,))
                    return "Successfully loaded module '%s'" % (mod_name,)

                irc_msg=irc_message.irc_message(client=self.client,nick=nick,username=username,host=host,
                                target=target,message=message,prefix=prefix,command=command,
                                user=user,access=access)

                m=self.helpre.search(command)
                if m:
                    return self.help(irc_msg,m.group(2))
                return self.run_commands(irc_msg)
        return None

    def scan(self, rand_id,nick,pnick, group_id):
        s = scan.scan(rand_id,self.client,self.conn,self.cursor,nick,pnick, group_id)
        s.run()

    # split off parse into a func?

    def run_commands(self,irc_msg):
        #if self.ctrl_list.has_key(command):
        #    k=command

        for k in self.ctrl_list.keys():
            ctrl=self.ctrl_list[k]
            #print "Trying key %s with obj of class '%s'" % (k,ctrl.__class__.__name__)

            try:
                if ctrl.execute(irc_msg.user,irc_msg.access,irc_msg):
                    return "Successfully executed command '%s' with key '%s'" % (ctrl.__class__.__name__,k)
            except Exception, e:
                del self.ctrl_list[k]
                print "Exception in "+ ctrl.__class__.__name__ +" module dumped"
                irc_msg.reply("Error in module '"+ ctrl.__class__.__name__ +"'. Please report the command you used to jester as soon as possible.")
                print e.__str__()
                traceback.print_exc()
                if DEBUG:
                    print "nick: '%s'" % (irc_msg.nick,)
                    print "username: '%s'" % (irc_msg.username,)
                    print "host: '%s'" % (irc_msg.host,)
                    print "target: '%s'" % (irc_msg.target,)
                    print "message: '%s'" % (irc_msg.message,)
                    print "prefix: '%s'" % (irc_msg.prefix,)
                    print "command: '%s'" % (irc_msg.command,)
                    print "user: '%s'" % (irc_msg.user,)
                    print "access: '%s'" % (irc_msg.access,)
                    err_msg=self.load_mod(k)
                    if err_msg:
                        irc_msg.reply("Unable to reload module '%s', this may seriously impede further use" % (k,))
                        print err_msg
        return None

    def load_mod(self,mod_name):
        try:
            if mod_name == 'loadable':
                loadable = reload(sys.modules['loadable'])
                self.reg_controllers()
                return None
            if mod_name == 'scan':
                scan = reload(sys.modules['scan'])
                return None
            if mod_name == 'galstatus':
                galstatus = reload(sys.modules['galstatus'])
                self.galstatus=galstatus.galstatus(self.client,self.conn,self.cursor,self.config)
                return None
            filename=os.path.join(self.mod_dir,mod_name+'.py')
            execfile(filename)
            self.ctrl_list[mod_name] = locals().get(mod_name)(self.cursor)
        except Exception, e:
            traceback.print_exc()
            return e.__str__()

        return None

    def help(self,irc_msg,param):
        if param:
            if self.ctrl_list.has_key(param):
                if irc_msg.access >= self.ctrl_list[param].level:
                    try:
                        #self.client.reply(prefix,nick,target,param+": "+self.ctrl_list[param].help())
                        self.ctrl_list[param].help(irc_msg.user,irc_msg.access,irc_msg)
                        return "Successfully executed help for '%s' with key '%s'" % (self.ctrl_list[param].__class__.__name__,param)
                    except Exception, e:
                        ctrl=self.ctrl_list[param]
                        del self.ctrl_list[param]
                        print "Exception in "+ ctrl.__class__.__name__ +" module dumped"
                        irc_msg.reply("Error in module '"+ ctrl.__class__.__name__ +"'. Please report the command you used to jester as soon as possible.")
                        print e.__str__()
                        traceback.print_exc()
                        if DEBUG:
                            print "nick: '%s'" % (irc_msg.nick,)
                            print "username: '%s'" % (irc_msg.username,)
                            print "host: '%s'" % (irc_msg.host,)
                            print "target: '%s'" % (irc_msg.target,)
                            print "message: '%s'" % (irc_msg.message,)
                            print "prefix: '%s'" % (irc_msg.prefix,)
                            print "command: '%s'" % (irc_msg.command,)
                            print "user: '%s'" % (irc_msg.user,)
                            print "access: '%s'" % (irc_msg.access,)
                            err_msg=self.load_mod(param)
                            if err_msg:
                                irc_msg.reply("Unable to reload module '%s', this may seriously impede further use" % (k,))
                                print err_msg
                        return
        irc_msg.reply("Munin help. For more information use: <"+self.notprefix.replace("|","")+self.pubprefix.replace("|","")+self.privprefix.replace("|","")+">help <command>. Built-in commands: help" + (bool(irc_msg.access>=1000) and ", loadmod" or ""))
        command_list=[]
        for ctrl in self.ctrl_list.values():
            if irc_msg.access >= ctrl.level:
                command_list.append(ctrl.__class__.__name__)
        command_list.sort()
        irc_msg.reply("Loaded modules: "+ ", ".join(command_list))


    def getpnick(self,host):
        m=self.pnickre.search(host)
        if m:
            return m.group(1).lower()
        else:
            return None

    def reg_controllers(self):
        for command_name in os.listdir(self.mod_dir):
            m=re.search("(.*)\.py$",command_name,re.I)
            if m:
                source=m.group(1)
                if source != "__init__":
                    filename=os.path.join(self.mod_dir, source+'.py')
                    execfile(filename)
                    if DEBUG: print "Loading %s\n" % source,
                    self.ctrl_list[source] = locals().get(source)(self.cursor)

    def prefix_to_numeric(self,prefix):
        if self.notprefix.replace("|","").find(prefix) > -1:
            return self.client.NOTICE_PREFIX
        if self.pubprefix.replace("|","").find(prefix) > -1:
            return self.client.PUBLIC_PREFIX
        if self.privprefix.replace("|","").find(prefix) > -1:
            return self.client.PRIVATE_PREFIX
        return -1
