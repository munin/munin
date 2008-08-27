#!/usr/bin/env python
"""
Put the ships from url into our database.
"""

import ConfigParser
import psycopg
import urllib2
import re

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
           "Cath": "Cathaar",
           "Zik": "Zikonian",
           "Xan": "Xandathrii"}

keys = ['name', 'class', 'target_1', 'target_2', 'target_3', 'type', 'init',
        'gun', 'armor', 'damage', 'empres', 'metal', 'crystal', 'eonium',
        'race']

regex = r'^<tr class="(Ter|Cath|Xan|Zik|Etd)">.+?(\w+)</td>' # race & name
regex += r'<td>(\w+)</td>' # class
regex += r'<td>(\w\w|\-)</td>'*3 # t1,t2,t3
regex += r'<td>(\w+)</td>' # type
regex += r'.+?(\d+|\-)</td>'*8 # some numbers
regex += r'.+?</tr>$' # end of the line
sre = re.compile(regex,re.I|re.M)

def main(url="http://game.planetarion.com/manual.php?page=stats"):
    """Parse url, and put the ships into our database."""

    config = ConfigParser.ConfigParser()
    if not config.read('muninrc'):
        print >> sys.stderr, "Error: Found no configuration file in ./muninrc."
        return 1
    DSN = "dbname=%s user=%s" % (config.get('Database', 'dbname'),
                                 config.get('Database', 'user'))
    if config.has_option('Database', 'password'):
        DSN += ' password=%s' % config.get('Database', 'password')
    connection = psycopg.connect(DSN)
    cursor = connection.cursor()

    stats = urllib2.urlopen(url).read()

    for line in sre.findall(stats):
        ship = {}
        for index, key in enumerate(keys):
            if line[index] in mapping:
                line[index] = mapping[line[index]]
            elif line[index].isdigit():
                line[index] = int(line[index])
            if line[index] != '-':
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
    sys.exit(main())
