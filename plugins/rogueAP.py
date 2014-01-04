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
import os
from includes.fonts import *

class Snoop(Thread):
    """This is an example plugin."""
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.RUN = True

        # Process arguments passed to module
        self.verb = kwargs.get('verbose', 0)
        self.fname = os.path.splitext(os.path.basename(__file__))[0]

    def run(self):
        while self.RUN:
            time.sleep(2)

    def is_ready(self):
        #Perform any functions that must complete before plugin runs
        return True

    def stop(self):
        self.RUN = False

    @staticmethod
    def get_parameter_list():
        info = {"info" : "Create a rogue access point.",
                "parameter_list" : [ ("ssid=<name>","The SSID of the acces point."),
                                     ("promis=[True|False]","Set promiscuous mode (respond to all probe requests)."),
                                     ("run_dhcp=[True|False]","Run a DHCP server."),
                                     ("local_nat=[True|False]","Run local NAT to route traffic out."),
                                     ("sslstrip=[True|False]","Send traffic through Moxie's SSL strip."),
                                     ("fakecert=[True|False]","Route SSL traffic to local fake cert")
                                    ]
                }
        return info


    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
#        #e.g of return data - [("tbl_name", [{'var01':99, 'var02':199}]
#        rtnData=[]
#        while self.data_store:
#            rtnData.append(self.data_store.popleft())
#        if rtnData:
#            return [("example_table", rtnData)]
#        else:
#            return []

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
