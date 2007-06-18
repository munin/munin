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

class res(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
    	self.paramre=re.compile(r"^\s+(\S+)\s+(\S+)\s+(\d+)\s+(\S+)")
        self.usage=self.__class__.__name__ + " <race> <govt> <reslab%> <tech>"
        self.helptext=None

    def execute(self,nick,username,host,target,prefix,command,user,access):
        m=self.commandre.search(command)
        if not m:
            return 0

        if access < self.level:
            self.client.reply(prefix,nick,target,"You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        reply=""
    	race=m.group(1)
        govt=m.group(2)
        reslab=int(m.group(3))
        tech=m.group(4)
        #reply = self.do_res(race,govt,reslab,tech)

        #self.client.reply(prefix,nick,target,reply)
        #return 1

        #def do_res(self, race, govt, reslab, tech):    
        racialmod = self.racial(race)
        govmod = self.gov(govt)
        techpoints = self.techpts(tech)	
        output = ""

        if racialmod == -1:
            self.client.reply(prefix,nick,target,"%s is not a race" % race)
            return 1

        if govmod == -1:
            self.client.reply(prefix,nick,target,"%s is not a government" % govt)
            return 1

        if reslab > 20:
            reslab = 20

        if techpoints == -1:
            self.client.reply(prefix,nick,target,"%s is not a valid technology" % tech)
            return 1
        lvlx = 5000
        zerox = 0

        for x in range(50):
            factor = x + govmod + reslab
            factor = float(factor)
            popgvt = 1 + (factor/100)
            tot = racialmod * popgvt		
            time = techpoints / tot
            final = math.floor(time)

            if x == 0:
		        zerox = final
		        self.client.reply(prefix,nick,target,"Base for %s / %s / %d / %s is: %d " % (race, govt, reslab, tech, zerox))
		        output += "Optimal researcher settings for this race/research: "
		        lvlx = zerox

            elif final < lvlx:
		        diff = final - zerox
		        output += "%d%% (%d | %dh), " % (x, diff, final)
		        lvlx = final

        if output:
            self.client.reply(prefix,nick,target,output)
        return 1


    #SILLY STUFF HERE TO GET THE NUMERICAL VALUES FOR ALL THE CRAP [PULL AUTOMAGICALLY FROM STATS?]
    def racial(self, race):
	   race = race.lower()
	   if race=="xan" or race=="xandathrii":
	       return 85

	   elif race=="cat" or race=="cathaar":
	       return 120

	   elif race=="zik" or race=="zikonian" or race=="ter" or race=="terran" or race=="etd" or race=="eitrades":
	       return 100

	   else:
	       return -1

    def gov(self, govt):
	    govt = govt.lower()
	    if govt=="feud" or govt=="feudalism":
		    return -25

	    elif govt=="dem" or govt=="demo" or govt=="democracy":
		    return 20

	    elif govt=="uni" or govt=="unification":
		    return -20

	    elif govt=="dic" or govt=="dict" or govt=="dictatorship":
		    return -20

	    elif govt=="none":
		    return 0

	    else:
		    return -1

    def techpts(self, tech):
	    t=tech.lower()

	    if t=="cov1" or t=="hct1":
		    return 1200

	    elif t=="tt1" or t=="infra1" or t=="scans1" or t=="cov2" or t=="hct2":
		    return 1600

	    elif t=="ships1" or t=="scans2" or t=="scans3" or t=="core1" or t=="cov3" or t=="hct3":
		    return 2400

	    elif t=="tt2" or t=="infra2" or t=="cov4":
		    return 3200

	    elif t=="scans4":
		    return 3600

	    elif t=="tt3" or t=="infra3" or t=="ships2" or t=="scans5" or t=="core2" or t=="cov5" or t=="hct4":
		    return 4800

	    elif t=="cov6" or t=="hct5":
		    return 6400

	    elif t=="infra4" or t=="ships3" or t=="scans 6" or t=="scans7" or t=="core3" or t=="hct6" or t=="hct7" or t=="hct8" or t=="hct9" or t=="hct10" or t=="hct11" or t=="hct12":
		    return 7200

	    elif t=="hct13" or t=="hct14" or t=="hct15" or t=="hct16":
		    return 9600

	    else:
		    return -1
