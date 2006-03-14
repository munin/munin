#!/usr/bin/python

import psycopg

conn=psycopg.connect("dbname=patools16 user=andreaja")
cursor=conn.cursor()

cursor.execute("DROP TABLE planet_dump")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE planet_canon")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE galaxy_dump")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE galaxy_canon")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE alliance_dump")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE alliance_canon")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

cursor.execute("DROP TABLE updates")
print cursor.statusmessage
if cursor.statusmessage != 'DROP TABLE':
    conn.rollback()
    raise

conn.commit()
