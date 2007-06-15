"""
Loadable.Loadable subclass
"""

class longshot(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1000)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(.*)")
        self.usage=self.__class__.__name__ + ""
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
	gals=m.group(1).split()
	
	query = "SELECT planets,count(*) AS count FROM " 
	query+= " (SELECT  x AS x,y AS y,count(*) AS planets from planet_dump"
	query+= " WHERE tick = (SELECT max_tick()) AND x < 200"
	query+= " GROUP BY x,y ORDER BY count(*) DESC) AS foo"
	query+= " GROUP BY planets ORDER BY planets ASC"

	reply=""
	self.cursor.execute(query)
	if self.cursor.rowcount>0:
	    res=self.cursor.dictfetchall()
	    gals=0
	    bracket=0
	    max_planets=0
	    max_planets_no_guarantee=0
	    
	    for r in res:
		gals+=res['count']
	    bracket=int(gals*.2)
	    for r in res:
		bracket-=r['count']
		if bracket < 0:
		    max_planets_no_guarantee=r['planets']
		    break
		max_planets=r['planets']
	else:
	    raise Exception("Gutted")
	
        if True:
            pass

        # do stuff here

        return 1
