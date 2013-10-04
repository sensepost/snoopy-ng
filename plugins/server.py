#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from sqlalchemy import create_engine, MetaData, Table, Column, String,\
                   select, and_, Integer
from collections import deque
from sqlalchemy.exc import *
from includes.common import *
import includes.common as common
import time
from datetime import datetime
from threading import Thread
import inspect
logging.basicConfig(level=logging.DEBUG, filename='/tmp/snoopy_server.log',
                format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
from includes import webserver
import os
#from includes import xbeeserver #TODO

#def get_plugins():
#    filename = os.path.split(inspect.getfile(inspect.currentframe()))[1].replace(".py","")
#    pluginNames = common.get_plugins()
#    pluginNames.remove("server")
#    plugins = []
#    for plug in pluginNames:
#        plug = "plugins." + plug
#        m = __import__(plug, fromlist="Snoop").Snoop
#        plugins.append(m)
#    return plugins

def get_plugins():
    filename = os.path.split(inspect.getfile(inspect.currentframe()))[1].replace(".py","")
    this_plugin = __import__("plugins." + filename, fromlist="Snoop").Snoop
    plugins = common.get_plugins()
    plugins.remove(this_plugin)
    return plugins

class Snoop(Thread):
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.RUN = True
        self.setDaemon(True)
        # Process arguments passed to module
        self.port = kwargs.get('port',9001)
        self.ip = kwargs.get('ip','0.0.0.0')
        self.db = kwargs.get('dbms',None)
        if self.db:
            self.metadata = MetaData(self.db)       #If you need to access the db object. N.B Use for *READ* only.
            self.metadata.reflect()
        self.data = deque(maxlen=100000)

    def run(self):
        logging.info("Running wbeserver on '%s:%s'" % (self.ip,self.port))
        webserver.run_webserver(self.port,self.ip)

    def is_ready(self):
        #Perform any functions that must complete before plugin runs
        return True

    def stop(self):
        self.RUN = False
        self._Thread__stop() #Ouch. Probably a bad approach.

    @staticmethod
    def get_parameter_list():
        info = {"info" : "Runs a server - allowing local data to be synchronized remotely.",
                "parameter_list" : [("port=<int>","The HTTP port to listen on."),
                                    ("xbee=<int>","The XBee PIN to listen on")
                                    ]
                }

        return info

    def get_data(self):
        return webserver.poll_data()

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        tables = []
        for plug in get_plugins():
            tables += plug.get_ident_tables()
        return tables

    @staticmethod
    def get_tables():
        tables=[]
        for plug in get_plugins():
            tbls = plug.get_tables()
            tables+=tbls
        return tables

if __name__ == "__main__":
    Snoop().start()
