#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlalchemy as sa
from threading import Thread
from includes.sakis import Sakis 

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class Snoop(Thread):
    def __init__(self, *args):
        Thread.__init__(self)
        self.RUN = True
        self.modemConn = None 
        if args and args[0] is not None:
            print args[0] 
            try:
                pargs=dict(a.split("=") for a in args[0])# for a in args[0][0].split(","))
                if 'APN' in pargs:
                    self.apn = pargs['APN']
            except Exception,e:
                logging.error("Bad arguments passed to module")
                print e

    def run(self):
        """Operations for module go here."""
        while self.RUN:
            try:
                self.modemConn = Sakis(self.apn)
            except Exception, e:
                logging.exception(e)
                time.sleep(10)

    def stop(self):
        self.RUN = False
        self.modemConn.stop()

    @staticmethod
    def get_parameter_list():
        return ["apn=<apn>. e.g. -m gsm:apn=orange.fr"]

    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        return []

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return []

    @staticmethod
    def get_tables():
        return []


if __name__ == "__main__":
    Snoop().start()
