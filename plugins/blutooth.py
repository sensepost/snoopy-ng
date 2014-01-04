#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
from sqlalchemy import MetaData, Table, Column, String, Unicode, Integer
from threading import Thread
import os
from includes.fonts import *


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class Snoop(Thread):
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.devices = {}
        self.RUN = True
        self.verb = kwargs.get('verbose', 0)
        self.fname = os.path.splitext(os.path.basename(__file__))[0]

    def run(self):
        from bluetooth import discover_devices
        logging.debug("Starting bluetooth module")
        reported = False
        while self.RUN:
            try:
                for addr, name in discover_devices(lookup_names=True):
                    name = name.decode('utf-8', 'ignore')
                    if (addr, name) not in self.devices:
                        self.devices[(addr, name)] = 0
                        if self.verb > 0:
                            logging.info("Sub-plugin %s%s%s observed new device: %s%s%s" % (GR,self.fname,G,GR,mac, G))
                reported = False
            except Exception,e:
                if not reported:
                    logging.error("Error accessing bluetooth device. Will keep checking for one, but will not report this error again. Check log file for more detail.")
                    logging.debug(e)
                    reported = True
            tmptimer = 0
            while self.RUN and tmptimer < 5:
                time.sleep(0.1)
                tmptimer += 0.1

    def stop(self):
        self.RUN = False

    def is_ready(self):
        return True

    @staticmethod
    def get_parameter_list():
        info = {"info" : "Discovers Bluetooth devices.",
                "parameter_list" : None
                }
        return info


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
    def get_tables():

        """Make sure to define your table here"""
        table = Table('bluetooth', MetaData(),
                           Column('mac', String(12), primary_key=True),
                           Column('name', Unicode(100), primary_key=True),
                           Column('sunc', Integer, default=0))


        return [table]


if __name__=="__main__":
    Snoop().start()
