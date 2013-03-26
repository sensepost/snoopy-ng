# -*- coding: utf-8 -*-
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
from sqlalchemy import *

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

class snarf():

    def __init__(self): 
        self.dict_device_bssids={}

    @staticmethod
    def get_tables():
        """Make sure to define your table here"""
        metadata=MetaData()
        table=Table('bssid_arps',metadata,
            Column('mac', String(12), primary_key=True),
            Column('bssid',String(12), primary_key=True),
            Column('sunc',Integer,default=0)
            )
        return [table]
    
    def proc_packet(self,p):
        if ( p.haslayer(ARP) and p.haslayer(Ether) ):
            mac=re.sub(':','',p.addr2)
            bssid=p[Ether].dst
            if ( bssid != 'ff:ff:ff:ff:ff:ff' ):
                self.dict_device_bssids[(mac,bssid)]=0

    def get_data(self):
        """Ensure data is returned in the form of a SQL row """

        tmp=[]
        sunc=[]
        for k,v in self.dict_device_bssids.iteritems():
            if v == 0:
                tmp.append( {"mac":k[0], "bssid":k[1]} )
                sunc.append((k[0],k[1]))        

        if len(sunc) > 0:
            for foo in sunc:
                mac,bssid=foo[0],foo[1]
                self.dict_device_bssids[(mac,bssid)]=1
            return ("bssid_arps",tmp)

        

