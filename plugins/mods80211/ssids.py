#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
from sqlalchemy import MetaData, Table, Column, Integer, String, Unicode
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import Dot11ProbeReq, Dot11Elt
from base64 import b64encode
from includes.common import snoop_hash

#N.B If you change b64mode to False, you should probably change
# the ssid colum to type Unicode.
b64mode = True

class Snarf():
    """SSID processor."""

    def __init__(self,hash_macs="False"):
        self.device_ssids = {}
        self.hash_macs = hash_macs

    @staticmethod
    def get_tables():
        """Make sure to define your table here"""
        table = Table('ssids', MetaData(),
                      Column('mac', String(64), primary_key=True), #Len 64 for sha256
                      Column('ssid', String(100), primary_key=True, autoincrement=False),
                      Column('sunc', Integer, default=0))
        return [table]

    def proc_packet(self, p):
        if p.haslayer(Dot11ProbeReq) and p[Dot11Elt].info != '':
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
                tmp.append( {"mac": k[0], "ssid": k[1]} )
                todel.append((k[0], k[1]))

        if len(todel) > 0:
            for foo in todel:
                mac, ssid = foo[0], foo[1]
                self.device_ssids[(mac, ssid)] = 1
            return ("ssids", tmp)
