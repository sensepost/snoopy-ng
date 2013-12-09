#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
from sqlalchemy import MetaData, Table, Column, Integer, String, Unicode
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import Dot11Beacon, Dot11Elt
from base64 import b64encode
from includes.common import snoop_hash
from collections import OrderedDict

#N.B If you change b64mode to False, you should probably change
# the ssid colum to type Unicode.
b64mode = False

MAX_NUM_SSIDs = 1000 #Maximum number of mac:ssid pairs to keep in memory

class Snarf():
    """Extract BSSIDs (i.e. Access Points"""

    def __init__(self, **kwargs):
        self.device_ssids = OrderedDict()
        #self.hash_macs = hash_macs

        self.hash_macs = kwargs.get('hash_macs', False)

    @staticmethod
    def get_tables():
        """Make sure to define your table here"""
        table = Table('bssids', MetaData(),
                      Column('mac', String(64), primary_key=True), #Len 64 for sha256
                      Column('bssid', String(100), primary_key=True, autoincrement=False),
                      Column('sunc', Integer, default=0))
        return [table]

    def proc_packet(self, p):
        if p.haslayer(Dot11Beacon) and p[Dot11Elt].info != '' and re.match("[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]", p.addr2):
            mac = re.sub(':', '', p.addr2)
            if self.hash_macs == "True":
                mac = snoop_hash(mac)
            if b64mode:
                ssid = b64encode(p[Dot11Elt].info)
            else:
                ssid = p[Dot11Elt].info.decode('utf-8', 'ignore')
            if (mac, ssid) not in self.device_ssids:
                self.device_ssids[(mac, ssid)] = 0

    def get_data(self):
        tmp = []
        todel = []
        for k, v in self.device_ssids.iteritems():
            if v == 0:
                tmp.append( {"mac": k[0], "bssid": k[1]} )
                todel.append((k[0], k[1]))

        # Reduce mac:ssid data structure if it's getting too large
        if len(self.device_ssids) > MAX_NUM_SSIDs:
            logging.debug("MAC:BSSID structure is large (%d), going to reduce by 50pc (-%d)" % (len(self.device_ssids),(int(0.5*MAX_NUM_SSIDs))))
            for i in range(int(0.5 * MAX_NUM_SSIDs)):
                try:
                    self.device_ssids.popitem(last = False)
                except KeyError:
                    pass
            logging.debug("MAC:BSSID structure is now %d" % len(self.device_ssids))

        if len(todel) > 0:
            for foo in todel:
                mac, ssid = foo[0], foo[1]
                self.device_ssids[(mac, ssid)] = 1
            return ("bssids", tmp)
