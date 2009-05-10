
#!/usr/bin/python

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

import sys

from psycopg2 import psycopg1 as psycopg
#!/usr/bin/python

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

import sys
import ConfigParser
from psycopg2 import psycopg1 as psycopg

config = ConfigParser.ConfigParser()
if not config.read("muninrc"):
    # No config found.
    raise ValueError("Expected configuration file muninrc"
                     ", not found.")

DSN = "dbname=%s user=%s" % (config.get("Database", "dbname"),
                             config.get("Database", "user"))
if config.has_option('Database', 'password'):
    DSN += ' password=%s' % config.get('Database', 'password')
if config.has_option('Database', 'host'):
    DSN += ' host=%s' % config.get('Database', 'host')

conn=psycopg.connect(DSN)
cursor=conn.cursor()

query='SELECT pnick, sponsor FROM user_list'
query+=" WHERE userlevel >= 100"
cursor.execute(query)
  
print "\n".join(map(lambda x: '"%s" -> "%s";'%(x['sponsor'],x['pnick']),cursor.dictfetchall()))
