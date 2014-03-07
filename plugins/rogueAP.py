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
from includes.rogee import *

class Snoop(Thread):
    """This is an example plugin."""
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.RUN = True

        # Process arguments passed to module
        self.verb = kwargs.get('verbose', 0)
        self.fname = os.path.splitext(os.path.basename(__file__))[0]

        self.myRogue = rogueAP(**kwargs)

    def run(self):
        self.myRogue.run_ap()
        self.myRogue.run_dhcpd()
        self.myRogue.do_nat()

        while self.RUN:
            if not self.myRogue.all_OK():
                logging.error("Something's gone wrong with the Rogue AP. Probably try restarting things.")
            time.sleep(2)

    def is_ready(self):
        #Perform any functions that must complete before plugin runs
        if not self.myRogue.all_OK():
            return False
        return True

    def stop(self):
        self.RUN = False
        self.myRogue.shutdown()

    @staticmethod
    def get_parameter_list():
        info = {"info" : "Create a rogue access point. - UNDER CONSTRUCTION",
                "parameter_list" : [ ("ssid=<name>","The SSID of the acces point."),
                                     ("promis=[True|False]","Set promiscuous mode (respond to all probe requests)."),
                                     ("run_dhcp=[True|False]","Run a DHCP server."),
                                     ("local_nat=[True|False]","Run local NAT to route traffic out."),
                                     ("sslstrip=[True|False]","Send traffic through Moxie's SSL strip.")
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
        return self.myRogue.get_new_leases()

    @staticmethod
    def get_tables():
        """This function should return a list of table(s)"""

        table = Table('dhcp_leases',MetaData(),
                              Column('leasetime', Integer),
                              Column('mac', String(12), primary_key=True),
                              Column('ip', String(length=20), primary_key=True, autoincrement=False),
                              Column('hostname', String(length=20)),
                              Column('sunc', Integer, default=0))   #Omit this if you don't want to sync
        return [table]

if __name__ == "__main__":
    Snoop().start()
