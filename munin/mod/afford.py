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

# This file has no alliance specific stuff as far as I can tell.
# qebab, 22/06/08

import re
from munin import loadable

class afford(loadable.loadable):
    def __init__(self,cursor):
        super(self.__class__,self).__init__(cursor,1)
        self.paramre=re.compile(r"^\s+(\d+)[. :-](\d+)[. :-](\d+)\s+(\S+)")
        self.usage=self.__class__.__name__ + " <x:y:z> <shipname>"
        self.helptext=None

    def execute(self,user,access,irc_msg):
        m=irc_msg.match_command(self.commandre)
        if not m:
            return 0

        if access < self.level:
            irc_msg.reply("You do not have enough access to use this command")
            return 0

        m=self.paramre.search(m.group(1))
        if not m:
            irc_msg.reply("Usage: %s" % (self.usage,))
            return 0

        # assign param variables
        reply=""
        x=m.group(1)
        y=m.group(2)
        z=m.group(3)
        ship_name=m.group(4)

        p=loadable.planet(x=x,y=y,z=z)
        if not p.load_most_recent(self.cursor):
            irc_msg.reply("No planet matching '%s:%s:%s' found"%(x,y,z))
            return 1

        query="SELECT tick,nick,scantype,rand_id,timestamp,roid_metal,roid_crystal,roid_eonium,res_metal,res_crystal,res_eonium"
        query+=", factory_usage_light, factory_usage_medium, factory_usage_heavy, prod_res"
        query+=" FROM scan AS t1 INNER JOIN planet AS t2 ON t1.id=t2.scan_id"
        query+=" WHERE t1.pid=%s ORDER BY timestamp DESC"
        self.cursor.execute(query,(p.id,))

        if self.cursor.rowcount < 1:
            reply+="No planet scans available on %s:%s:%s" % (p.x,p.y,p.z)
        else:
            s=self.cursor.dictfetchone()
            tick=s['tick']
            res_m=int(s['res_metal'])
            res_c=int(s['res_crystal'])
            res_e=int(s['res_eonium'])
            prod_res=int(s['prod_res'])
            rand_id=s['rand_id']

            query="SELECT name,class,metal,crystal,eonium,total_cost"
            query+=" FROM ship WHERE name ilike %s LIMIT 1"
            self.cursor.execute(query,('%'+ship_name+'%',))

            if self.cursor.rowcount<1:
                reply="%s is not a ship" % (ship_name,)
            else:
                ship=self.cursor.dictfetchone()
                cost_m=ship['metal']
                cost_c=ship['crystal']
                cost_e=ship['eonium']
                total_cost=ship['total_cost']
                class_factory_table = {'Fighter': 'factory_usage_light', 'Corvette': 'factory_usage_light', 'Frigate': 'factory_usage_medium',
                                       'Destroyer': 'factory_usage_medium', 'Cruiser': 'factory_usage_heavy', 'Battleship': 'factory_usage_heavy'}
                prod_modifier_table = {'None': 0, 'Low': 33, 'Medium': 66, 'High': 100}
                
                capped_number=min(res_m/cost_m, res_c/cost_c, res_e/cost_e)
                overflow=res_m+res_c+res_e-(capped_number*(cost_m+cost_c+cost_e))
                buildable = capped_number + ((overflow*.95)/total_cost)


                demo_modifier=1/(1-float(self.config.get('Planetarion', 'democracy')))
                tota_modifier=1/(1-float(self.config.get('Planetarion', 'totalitarianism')))
                reply+="Newest planet scan on %s:%s:%s (id: %s, pt: %s)" % (p.x,p.y,p.z,rand_id,tick)
                reply+=" can purchase %s: %s | Democracy: %s | Totalitarianism: %s"%(ship['name'],
                                                                                     int(buildable),
                                                                                     int(buildable*demo_modifier), 
                                                                                     int(buildable*tota_modifier))

                if prod_res > 0:
                    factory_usage=s[class_factory_table[ship['class']]]
                    max_prod_modifier=prod_modifier_table[factory_usage]
                    buildable_from_prod = buildable + max_prod_modifier*(prod_res)/100/total_cost
                    reply+=" Counting %d res in prod at %s usage:" % (prod_res,factory_usage)
                    reply+=" %s | Democracy: %s | Totalitarianism: %s"%(int(buildable_from_prod), 
                                                                        int(buildable_from_prod*demo_modifier),
                                                                        int(buildable_from_prod*tota_modifier))

        irc_msg.reply(reply)
        return 1
