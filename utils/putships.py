#!/usr/bin/env python
"""
Put the ships from url into our database.
"""

import configparser
from psycopg2 import psycopg1 as psycopg
import urllib.request, urllib.error, urllib.parse
import re
import sys
import argparse

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
           "Re": "Rs"  # Resources
           }

keys = ['race', 'name', 'class', 'target_1', 'target_2', 'target_3', 'type', 'init',
        'gun', 'armor', 'damage', 'empres', 'metal', 'crystal', 'eonium']

regex = r'^<tr class="(Ter|Cat|Xan|Zik|Etd)">.+?>([^<]+)</td>'  # race & name
regex += r'<td>(\w+)</td>'  # class
regex += r'(?:<td>(\w\w|\-)</td>)?' * 3  # t1,t2,t3
regex += r'<td>(\w+)</td>'  # type
regex += r'.+?(\d+|\-)</td>' * 8  # some numbers
regex += r'.+?</tr>$'  # end of the line
sre = re.compile(regex, re.I | re.M)


def main():
    """Parse url, and put the ships into our database."""

    config = configparser.ConfigParser()
    if not config.read('muninrc'):
        print("Error: Found no configuration file in ./muninrc.", file=sys.stderr)
        return 1
    DSN = "dbname=%s user=%s" % (config.get('Database', 'dbname'),
                                 config.get('Database', 'user'))
    if config.has_option('Database', 'password'):
        DSN += ' password=%s' % config.get('Database', 'password')
    if config.has_option('Database', 'host'):
        DSN += ' host=%s' % config.get('Database', 'host')
    connection = psycopg.connect(DSN)
    cursor = connection.cursor()

    parser = argparse.ArgumentParser(description='Planetarion ship stats importer for Munin.')
    default_round = config.getint('Planetarion', 'current_round')
    default_stats = 'https://game.planetarion.com/manual.pl?page=stats'
    parser.add_argument('-r', '--round', type=int, default=default_round,
                        help="Default: the value of 'Planetarion/current_round' in muninrc (%s)" % (default_round))
    parser.add_argument('-u', '--url', default=default_stats,
                        help="Default: %s" % (default_stats))
    args = parser.parse_args()

    useragent = "Munin (Python-urllib/%s); BotNick/%s; Admin/%s" % (urllib2.__version__,
                                                                    config.get("Connection", "nick"), config.get("Auth", "owner_nick"))

    cursor.execute("DELETE FROM ship WHERE round=%s;", (args.round,))

    req = urllib.request.Request(args.url)
    req.add_header('User-Agent', useragent)
    stats = urllib.request.urlopen(req).read()

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
        if ship['type'] == 'EMP':
            ship['type'] = 'Emp'
        fields = ['round']
        params = [args.round]
        for key in ship:
            fields.append(key)
            params.append(ship[key])
        query = QUERY % (', '.join(fields),
                         ', '.join(len(params) * ['%s']))
        cursor.execute(query, tuple(params))
    connection.commit()


if __name__ == '__main__':
    main()
