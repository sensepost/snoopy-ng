#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
from sqlalchemy import MetaData, Table, Column, Integer, String, Unicode
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *#Dot11ProbeReq, Dot11Elt, TCP, addr2
from base64 import b64encode
from includes.common import snoop_hash
from collections import OrderedDict

MAX_NUM_GUIDs = 1000 #Maximum number of mac:guid paris to keep in memory

class Snarf():
    """Apple devices emit a GUID when joining a network. This captures it."""

    def __init__(self, **kwargs):
        self.apple_guids = OrderedDict()

        #Process passed parameters
        self.hash_macs = kwargs.get('hash_macs', False)
        self.drone = kwargs.get('drone',"no_drone_name_supplied")
        self.run_id = kwargs.get('run_id', "no_run_id_supplied")
        self.location = kwargs.get('location', "no_location_supplied")

    @staticmethod
    def get_tables():
        """Make sure to define your table here"""
        table = Table('apple_guids', MetaData(),
                      Column('mac', String(64), primary_key=True), #Len 64 for sha256
                      Column('guid', String(100), primary_key=True, autoincrement=False),
                      Column('sunc', Integer, default=0))
        return [table]

    def proc_packet(self, p):
        if p.haslayer(Ether) and p.haslayer(TCP) and hasattr(p[TCP], 'load'):
            data=p[TCP].load
            #mac = re.sub(':', '', p.addr2)
            mac = re.sub(':', '', p[Ether].src)
            if self.hash_macs == "True":
                mac = snoop_hash(mac)
            srl = re.search('(\$\w{8}-\w{4}-\w{4}-\w{4}-\w{13})', data)
            if srl:
                guid = srl.group(1)
                if (mac, guid) not in self.apple_guids:
                    self.apple_guids[(mac, guid)] = 0

    def get_data(self):
        tmp = []
        todel = []
        for k, v in self.apple_guids.iteritems():
            if v == 0:
                tmp.append( {"mac": k[0], "guid": k[1]} )
                todel.append((k[0], k[1]))

        # Reduce mac:guid data structure if it's getting too large
        if len(self.apple_guids) > MAX_NUM_GUIDs:
            logging.debug("MAC:GUID structure is large (%d), going to reduce by 50pc (-%d)" % (len(self.apple_guids),(int(0.5*MAX_NUM_GUIDs))))
            for i in range(int(0.5 * MAX_NUM_GUIDs)):
                try:
                    self.apple_guids.popitem(last = False)
                except KeyError:
                    pass
            logging.debug("MAC:GUID structure is now %d" % len(self.apple_guids))

        if len(todel) > 0:
            for foo in todel:
                mac, guid = foo[0], foo[1]
                self.apple_guids[(mac, guid)] = 1
            return ("apple_guids", tmp)
