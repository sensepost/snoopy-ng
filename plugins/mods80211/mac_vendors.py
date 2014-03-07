#/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
from sqlalchemy import MetaData, Table, Column, Integer, String, Unicode
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import Dot11ProbeReq, Dot11Elt
from includes.common import snoop_hash
from includes.mac_vendor import mac_vendor
from collections import OrderedDict
import os
from includes.fonts import *

MAX_NUM_VENDORS = 1000

class Snarf():
    """Looks up vendors from MAC addresses."""

    def __init__(self, **kwargs):
        self.device_vendor = OrderedDict()
        #self.hash_macs = hash_macs
        self.mv = mac_vendor()

        self.hash_macs = kwargs.get('hash_macs', False)
        self.verb = kwargs.get('verbose', 0)
        self.fname = os.path.splitext(os.path.basename(__file__))[0]

    @staticmethod
    def get_tables():
        """Make sure to define your table here"""
        table = Table('vendors', MetaData(),
                      Column('mac', String(64), primary_key=True), #Len 64 for sha256
                      Column('vendor', String(20) ),
                      Column('vendorLong', String(50) ),
                      Column('sunc', Integer, default=0))
        return [table]

    def proc_packet(self, p):
        if p.haslayer(Dot11ProbeReq):
            mac = re.sub(':', '', p.addr2)
            vendor = self.mv.lookup(mac[:6])
            if self.hash_macs == "True":
                mac = snoop_hash(mac)

            if (mac, vendor) not in self.device_vendor:
                self.device_vendor[(mac, vendor)] = 0
                if self.verb > 0:
                    logging.info("Sub-plugin %s%s%s noted device %s%s%s is of type %s%s%s" % (GR,self.fname,G,GR,mac,G,GR,vendor[0],G))

    def get_data(self):

        new_data = []
        mark_as_done = []
        for macven, sunc in self.device_vendor.iteritems():
            try:
                mac = macven[0]
                vendor = macven[1][0]
                vendorLong = macven[1][1]
                if sunc == 0:
                    new_data.append( {"mac": mac, "vendor": vendor, "vendorLong": vendorLong} )
                    mark_as_done.append( (mac,(vendor,vendorLong))  )
            except Exception, e:
                logging.error(e)
                logging.error(macven)


        # If we're reached the maximum, reduce by 50%
        if len( self.device_vendor ) > MAX_NUM_VENDORS:
            logging.debug("Vendor list has reached %d, reducing by 50pc" %len(self.device_vendor) )
            for i in range(int(0.5 * MAX_NUM_VENDORS)):
                try:
                    self.device_vendor.popitem(last = False)
                except KeyError:
                    pass
            logging.debug("New vendor list size is %d" %len(self.device_vendor))

        if len( mark_as_done ) > 0:
            for macven in mark_as_done:
                mac,vendor,vendorLong = macven[0], macven[1][0], macven[1][1]
                self.device_vendor[(mac,(vendor,vendorLong))] = 1
            return ("vendors", new_data)
