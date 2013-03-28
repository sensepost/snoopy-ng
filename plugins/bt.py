#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
from bluetooth import discover_devices
from sqlalchemy import MetaData, Table, Column, String, Unicode, Integer
from threading import Thread


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class Snoop(Thread):
    def __init__(self, *args):
        Thread.__init__(self)
        self.devices = {}
        self.RUN = True

    def run(self):
        logging.debug("Starting bluetooth module")
        while self.RUN:
            for addr, name in discover_devices(lookup_names=True):
                name = name.decode('utf-8', 'ignore')
                if (addr, name) not in self.devices:
                    self.devices[(addr, name)] = 0

            tmptimer = 0
            while self.RUN and tmptimer < 5:
                time.sleep(0.1)
                tmptimer += 0.1

    def stop(self):
        self.RUN = False

    @staticmethod
    def get_parameter_list():
        return ["None"]

    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        tmp = []
        todel = []
        for k, v in self.devices.iteritems():
            if v == 0:
                tmp.append({"mac": k[0], "name": k[1]})
                todel.append((k[0], k[1]))

        if todel:
            for foo in todel:
                mac, name = foo[0], foo[1]
                self.devices[(mac, name)] = 1
            return [("bluetooth", tmp)]
        return []

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return []
        #return ['bluetooth']
    
    @staticmethod
    def get_tables():

        """Make sure to define your table here"""
        table = Table('bluetooth', MetaData(),
                           Column('mac', String(12), primary_key=True),
                           Column('name', Unicode, primary_key=True),
                           Column('sunc', Integer, default=0))


        return [table]


if __name__=="__main__":
    Snoop().start()
