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
from gps import *#gps, WATCH_ENABLE
from math import isnan

class Snoop(Thread):
    """Gets GPS co-ordinates of drone using gpsd."""
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.RUN = True
        self.data_store = deque(maxlen=1000)

        # Process arguments passed to module
        self.drone = kwargs.get('drone',"no_drone_name_supplied")
        self.run_id = kwargs.get('run_id', "no_run_id_supplied")
        self.location = kwargs.get('location', "no_location_supplied")
        self.freq = kwargs.get('freq', 30)
        self.gpsd = None

    def poll(self):
        try:
            if not self.gpsd:
                self.gpsd = gps(mode=WATCH_ENABLE)
            self.gpsd.next()
        except Exception, e:
            logging.error("Unable to poll gpsd. Is it running? Error was '%s'"%e)
            return False
        else:
            return True

    def run(self):
        while self.RUN:
            if self.poll():
                lat,long,alt,speed,epx,epy = self.gpsd.fix.latitude, self.gpsd.fix.longitude, self.gpsd.fix.altitude, self.gpsd.fix.speed, self.gpsd.fix.epx, self.gpsd.fix.epy
                gtime = self.gpsd.utc,' + ', self.gpsd.fix.time

                #if (not isnan(epx) and not isnan(epy)) and (epx < 30 and epy < 30):
                if epx < 30 and epy < 30:
                    now = datetime.datetime.now()
                    self.data_store.append({"lat":lat, "long":long, "speed":speed, "epx":epx,"epy":epy, "timestamp":now})
                else:
                    logging.debug("No good signal on GPS yet... (epx=%f, epy=%f)"%(epx,epy))

                for i in range(self.freq+1):
                    self.poll()
                    time.sleep(1)
            else:
                time.sleep(10)

    def is_ready(self):
        #Perform any functions that must complete before plugin runs
        return True

    def stop(self):
        self.RUN = False

    @staticmethod
    def get_parameter_list():
        info = {"info" : "Queries gpsd server for GPS co-ordinates. Ensure the gpsd daemon is running, and on port 2947.",
                "parameter_list" : [ ("freq=<seconds>","Frequency to poll GPS. Set to 0 to get one fix, and end.") ]
                }
        return info


    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        #e.g of return data - [("tbl_name", [{'var01':99, 'var02':199}]
        rtnData=[]
        while self.data_store:
            rtnData.append(self.data_store.popleft())
        if rtnData:
            return [("gpsd", rtnData)]
        else:
            return []

    @staticmethod
    def get_tables():
        """This function should return a list of table(s)"""

        table = Table('gpsd',MetaData(),
                            Column('drone', String(length=20)),
                            Column('timestamp', DateTime, default='' ),
                            Column('lat', Float()),
                            Column('long', Float()),
                            Column('speed', Float()),
                            Column('epx', Float()),
                            Column('epy', Float()))
        return [table]

if __name__ == "__main__":
    Snoop().start()
