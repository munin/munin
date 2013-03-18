#!/usr/bin/env python
"""
Put the ships from url into our database.
"""

import ConfigParser
from psycopg2 import psycopg1 as psycopg
import urllib2
import re
import sys

QUERY = """
INSERT INTO ship(%s)
VALUES(%s)"""

mapping = {"Fi": "Fighter",
           "Co": "Corvette",
           "Fr": "Frigate",
           "De": "Destroyer",
           "Cr": "Cruiser",
           "Bs": "Battleship",
           "Ro": "Roids",
           "St": "Struct",
           "Ter": "Terran",
           "Etd": "Eitraides",
           "Cat": "Cathaar",
           "Zik": "Zikonian",
           "Xan": "Xandathrii",
           "Re":  "Rs" # Resources
           }

keys = ['race', 'name', 'class', 'target_1', 'target_2', 'target_3', 'type', 'init',
        'gun', 'armor', 'damage', 'empres', 'metal', 'crystal', 'eonium']

regex = r'^<tr class="(Ter|Cat|Xan|Zik|Etd)">.+?>([^<]+)</td>' # race & name
regex += r'<td>(\w+)</td>' # class
regex += r'(?:<td>(\w\w|\-)</td>)?'*3 # t1,t2,t3
regex += r'<td>(\w+)</td>' # type
regex += r'.+?(\d+|\-)</td>'*8 # some numbers
regex += r'.+?</tr>$' # end of the line
sre = re.compile(regex,re.I|re.M)

def main(url="http://game.planetarion.com/manual.pl?page=stats"):
    """Parse url, and put the ships into our database."""

    config = ConfigParser.ConfigParser()
    if not config.read('muninrc'):
        print >> sys.stderr, "Error: Found no configuration file in ./muninrc."
        return 1
    DSN = "dbname=%s user=%s" % (config.get('Database', 'dbname'),
                                 config.get('Database', 'user'))
    if config.has_option('Database', 'password'):
        DSN += ' password=%s' % config.get('Database', 'password')
    if config.has_option('Database', 'host'):
        DSN += ' host=%s' % config.get('Database', 'host')
    connection = psycopg.connect(DSN)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM ship;")
    cursor.execute("SELECT setval('ship_id_seq', 1, false);")

    stats = urllib2.urlopen(url).read()

    for line in sre.findall(stats):
        line = list(line)
        ship = {}
        for index, key in enumerate(keys):
            if line[index] in mapping:
                line[index] = mapping[line[index]]
            elif line[index].isdigit():
                line[index] = int(line[index])
            if line[index] not in ('-', '',):
                ship[key] = line[index]
        ship['total_cost'] = ship['metal'] + ship['crystal'] + ship['eonium']
        fields = []
        params = []
        for key in ship:
            fields.append(key)
            params.append(ship[key])
        query = QUERY % (', '.join(fields),
                         ', '.join(len(params) * ['%s']))
        cursor.execute(query, tuple(params))
    connection.commit()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(main(url=sys.argv[1]))
    else:
        sys.exit(main())
