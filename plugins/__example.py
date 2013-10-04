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

class Snoop(Thread):
    """This is an example plugin."""
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.RUN = True
        self.data_store = deque(maxlen=1000)

        # Process arguments passed to module
        self.var01 = kwargs.get('var01','default01')
        self.var02 = kwargs.get('var02','default02')

        self.db = kwargs.get('dbms',None)
        if self.db:
            self.metadata = MetaData(self.db)       #If you need to access the db object. N.B Use for *READ* only.
            self.metadata.reflect()

    def run(self):
        while self.RUN:
            new_value = randint(1,52) #Pick a card, any card
            now = datetime.datetime.now()
            self.data_store.append({'var01':self.var01, 'time':now, 'rand_num':new_value})
            logging.debug("Added %d" % new_value)
            time.sleep(2)

    def is_ready(self):
        #Perform any functions that must complete before plugin runs
        return True

    def stop(self):
        self.RUN = False

    @staticmethod
    def get_parameter_list():
        info = {"info" : "This is a test plugin. Testing 1,2,3. Can you hear me?",
                "parameter_list" : [ ("x=<y>","Test parameter one."),
                                     ("v=[True|False]","Test parameter two.")]
                }
        return info


    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        #e.g of return data - [("tbl_name", [{'var01':99, 'var02':199}]
        rtnData=[]
        while self.data_store:
            rtnData.append(self.data_store.popleft())
        if rtnData:
            return [("example_table", rtnData)]
        else:
            return []

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return []

    @staticmethod
    def get_tables():
        """This function should return a list of table(s)"""

        table = Table('example_table',MetaData(),
                              Column('time', DateTime, default='' ),
                              Column('rand_num', Integer, default='' ),
                              Column('var01', String(length=20)),
                              Column('var02', String(length=20)))
        return [table]

if __name__ == "__main__":
    Snoop().start()
