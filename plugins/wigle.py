#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from sqlalchemy import Float, DateTime, String, Integer, Table, MetaData, Column, select, outerjoin
from threading import Thread
from collections import deque
import os
import time
from includes.wigle_api_lite import fetchLocations
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class Snoop(Thread):
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.RUN = True
        self.CHECK_FREQ = 15    #Check every n seconds for new SSIDs
        self.ssids_to_lookup = deque()
        self.ssid_addresses = deque()
        self.bad_ssids = {}
        self.current_lookup = ''
        self.successfully_geolocated = deque()
        self.recently_found = deque(maxlen=1000)    #We keep a register of the last 1000, to prevent superfluous lookups before results make it into the db

        # Process arguments passed to module
        self.username = kwargs.get('username','NoUserNameSupplied')
        self.password = kwargs.get('password','NoPasswordSupplied')
        self.db = kwargs.get('dbms',None)

        self.last_checked = 0
        self.metadata = MetaData(self.db)
        self.metadata.reflect()
#        self.metadata = MetaData(self.db)
#        self.metadata.reflect()
#        t_wigle = self.metadata.tables['wigle']
#        t_ssids = self.metadata.tables['ssids']

    def querydb(self):
        wigle = self.metadata.tables['wigle']
        ssids = self.metadata.tables['ssids']
        now = os.times()[4]
        if now - self.last_checked > self.CHECK_FREQ:
            s = outerjoin(ssids,wigle, ssids.c.ssid==wigle.c.ssid).select(wigle.c.ssid == None)
            r = self.db.execute(s)
            results = r.fetchall()
            new_ssids = [t[1] for t in results] #Second field in each result row
            for ssid in new_ssids:
                if ssid not in self.ssids_to_lookup and ssid != self.current_lookup and ssid not in self.recently_found:
                    if ssid in self.bad_ssids and self.bad_ssids[ssid] > 2:
                        logging.debug("Ignoring bad SSID '%s' after %d failed lookups" %(ssid, self.bad_ssids[ssid]))
                    else:
                        self.ssids_to_lookup.append(ssid)
            self.last_checked = now
            if len(self.ssids_to_lookup) > 0:
                logging.debug("SSID lookup queue has %d SSIDs to query" % len(self.ssids_to_lookup))

    def run(self):
        """Thread runs independently looking up SSIDs"""
        wigle = self.metadata.tables['wigle']
        while self.RUN:
            try:
                self.current_lookup = self.ssids_to_lookup.popleft()
            except IndexError:
                pass
            else:
                if self.bad_ssids.get(self.current_lookup) > 2:
                    logging.debug("Ignoring bad SSID '%s'" % self.current_lookup)
                else:
                    locations = fetchLocations(self.current_lookup)
                    if locations == None:
                        logging.info("Wigle account has been shunned, backing off for 20 minutes")
                        time.sleep(60*20)
                        self.ssids_to_lookup.append(self.current_lookup)
                    elif 'error' in locations:
                        if 'Unable to login' in locations['error']:
                            logging.error("Unable to login to Wigle - check your credentials")
                            self.ssids_to_lookup.append(self.current_lookup)
                        else:
                            logging.error("An error occured whilst looking up SSID '%s', will retry in 5 seconds (Error: '%s')" %(self.current_lookup,locations['error']))
                            if self.current_lookup not in self.bad_ssids:
                                self.bad_ssids[self.current_lookup] = 0
                            self.bad_ssids[self.current_lookup] += 1
                            time.sleep(5)
                            self.ssids_to_lookup.append(self.current_lookup)
                    else:
                        self.recently_found.append(self.current_lookup)
                        for location in locations:
                            #for k in wigle.columns.keys():
                            #    if k not in locations:
                            #        location[k] = '' #Ensure no mising keys
                            self.successfully_geolocated.append( location )
            time.sleep(2)

    def is_ready(self):
        #Wait to ensure tables exist
        while True:
            try:
                self.metadata.reflect()
                wigle = self.metadata.tables['wigle']
                ssids = self.metadata.tables['ssids']
            except KeyError:
                time.sleep(1)
            else:
                break
        time.sleep(2)
        return True

    def stop(self):
        self.RUN = False

    @staticmethod
    def get_parameter_list():
        info = {"info" : "Looks up SSID locations via Wigle (from the ssid table). Ensure credentials are in 'wigle_creds.txt' in the ./includes/ folder.",
                "parameter_list" : None
                }
        return info

    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        # First we query the DB for fresh SSIDs, as we can have our own lock
        #  then we return any data that may have been found from the previous operation
        self.querydb()
        data = []
        while self.successfully_geolocated: data.append(self.successfully_geolocated.pop())

        if data:
            return [("wigle", data)]
        else:
            return []

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return []

    @staticmethod
    def get_tables():

        table = Table('wigle',MetaData(),
                              Column('ssid', String(length=100) ),
                              Column('lat', Float(), default=999 ),
                              Column('long', Float(), default=999 ),
                              Column('last_update', Integer, default=0 ),
                              Column('mac', String(length=18), default='' ),
                              Column('overflow', Integer),
                              Column('longaddress', String(length=150),default='' ),
                              Column('shortaddress', String(length=50),default='' ),
                              Column('city', String(length=50),default='' ),
                              Column('code', String(length=50), default='' ),
                              Column('country', String(length=50), default=''),
                              Column('county', String(length=50), default='' ),
                              Column('postcode', String(length=10), default='' ),
                              Column('road', String(length=50), default='' ),
                              Column('state', String(length=50), default='' ),
                              Column('suburb', String(length=50), default='' ),
                              Column('sunc', Integer, default=0))
        return [table]


if __name__ == "__main__":
    Snoop().start()
