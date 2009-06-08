from listener import auth
from listener import command
from listener import custom_runner
import mod
from psycopg2 import psycopg1 as psycopg

class ircu_router(object):
    def __init__(self,client,config,loader):


        self.client=client
        self.config=config
        self.conn = self.create_db_connection(config)
        self.cursor = self.conn.cursor()

        self.listeners=[
            command.command(client,self.cursor,mod,loader),
            custom_runner.custom_runner(client,self.cursor,config),
            auth.auth(client,config)
            ]

    def run(self):
        while 1:
            line = self.client.rline()
            if not line:
                break
            self.trigger_listeners(line)

    def trigger_listeners(self,line):
        for l in self.listeners:
            l.message(line)

    def create_db_connection(self,config):
        dsn = 'user=%s dbname=%s' % (config.get("Database", "user"), config.get("Database", "dbname"))
        if config.has_option("Database", "password"):
            dsn += ' password=%s' % config.get("Database", "password")
        if config.has_option("Database", "host"):
            dsn += ' host=%s' % config.get("Database", "host")

        conn=psycopg.connect(dsn)
        conn.autocommit(1)
        return conn
