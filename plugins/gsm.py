#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from threading import Thread
from includes.sakis import Sakis 
import time
import os
from sqlalchemy import MetaData, Table, Column, String, Unicode, Integer

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class Snoop(Thread):
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.RUN = True
        self.modemConn = None 
        self.time_started = os.times()[4]

        # Process arguments passed to module
        self.apn = kwargs.get('APN',None)
        if not self.apn:
            logging.error("No APN supplied")
            exit()

    def run(self):
        """Operations for module go here."""

        while self.RUN:
            try:
                self.modemConn = Sakis(self.apn, True)
                self.modemConn.join()
            except Exception, e:
                logging.exception(e)
                time.sleep(10)

    def stop(self):
        self.RUN = False
        self.modemConn.stop()

    def is_ready(self):
        if os.times()[4] - self.time_started > 10:    #Avoid calling this heavy function too often
            if self.modemConn.status() == "Connected":
                return True

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
