#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from sqlalchemy import Float, DateTime, String, Integer, Table, MetaData, Column #As required
from threading import Thread
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
import time
from collections import deque
from random import randint
import datetime
from threading import Thread
import datetime

class Snoop(Thread):
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.RUN = True

        # Process arguments passed to module
        self.drone = kwargs.get('drone',"no_drone_name_supplied")
        self.run_id = kwargs.get('run_id', "no_run_id_supplied")
        self.location = kwargs.get('location', "no_location_supplied")

        now = datetime.datetime.now() #.strftime("%Y-%m-%d %H:%M:%S")
        self.run_session = {"run_id" : self.run_id, "drone" : self.drone, "location" : self.location, "start" : now, "end" : now }


    def run(self):
        while self.RUN:
            time.sleep(1)

    def is_ready(self):
        return True

    def stop(self):
        self.RUN = False

    @staticmethod
    def get_parameter_list():
        info = {"info" : "Creates a 'session' identifier, noting the start and end time of running the program.",
                "parameter_list" : None
                }
        return info

    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        self.run_session['end'] = datetime.datetime.now() #.strftime("%Y-%m-%d %H:%M:%S")
        return [("session", [self.run_session])]

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return []

    @staticmethod
    def get_tables():
        """This function should return a list of table(s)"""
        run = Table('session', MetaData(),
                    Column('run_id', String(length=11), primary_key=True),
                    Column('location', String(length=60)),
                    Column('drone', String(length=20)),
                    Column('start', DateTime),
                    Column('end', DateTime))


        return [run]

if __name__ == "__main__":
    Snoop().start()
