"""
Loadable.Loadable subclass
"""

class launch(loadable.loadable):
    def __init__(self,client,conn,cursor):
        loadable.loadable.__init__(self,client,conn,cursor,1)
        self.commandre=re.compile(r"^"+self.__class__.__name__+"(.*)")
        self.paramre=re.compile(r"^\s+(\S+|\d+)\s+(\d+)")
        self.usage=self.__class__.__name__ + " <class|eta> <land_tick>"
        self.helptext=["Calculate launch tick, launch time, prelaunch tick and prelaunch modifier for a given ship class or eta, and land tick."]

        self.class_eta = {"fi": 8,
                          "co": 8,
                          "fr": 9,
                          "de": 9,
                          "cr": 10,
                          "bs": 10}

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


        eta = m.group(1)
        land_tick = int(m.group(2))

        if eta.lower() in self.class_eta.keys():
             eta = self.class_eta[eta.lower()]
        else:
            try:
                eta = int(eta)
            except ValueError:
                self.client.reply(prefix,nick,target,"Usage: %s" % (self.usage,))
                return 0

        query="SELECT max_tick()"
        try:
            self.cursor.execute(query)
            current_tick = self.cursor.dictfetchone()
        except psycopg.IntegrityError:
            self.client.reply(prefix,nick,target,"Could not fetch current tick.")
            return 0
        current_tick = current_tick['max_tick']

        current_time = datetime.datetime.utcnow()
        launch_tick = land_tick - eta
        launch_time = current_time + datetime.timedelta(hours=(launch_tick-current_tick))
        prelaunch_tick = land_tick - eta + 1
        prelaunch_mod = launch_tick - current_tick

        self.client.reply(prefix,nick,target,"eta %d landing pt %d (currently %d) must launch at pt %d (%s), or with prelaunch tick %d (currently %+d)" % (eta, land_tick, current_tick, launch_tick, (launch_time.strftime("%m-%d %H:55")), prelaunch_tick, prelaunch_mod))

        return 1