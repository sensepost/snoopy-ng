#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlalchemy as sa
from threading import Thread


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class Snoop(Thread):
    def __init__(self, *args):
        Thread.__init__(self)
        self.RUN = True
        self.username=''
        self.password=''
        self.db='snoopy.db'

        if args and args[0] is not None:
            try:
                pargs=dict(a.split("=") for a in args[0])# for a in args[0][0].split(","))
                if 'username' in pargs:
                    self.iface = pargs['iface']
                if 'password' in pargs and pargs['mon'].lower()=="true":
                    self.enable_monitor_mode = True
                if 'db' in pargs:
                    self.bfilter = pargs['filter']
            except:
                logging.error("Bad arguments passed to module")


    def run(self):
        while self.RUN:



    def stop(self):
        self.RUN = False

    @staticmethod
    def get_parameter_list():
        return ["None"]

    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        return []

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return [self.table]

    @staticmethod
    def get_tables():
        return []


if __name__ == "__main__":
    Snoop().start()
