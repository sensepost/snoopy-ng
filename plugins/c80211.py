# -*- coding: utf-8 -*-
from threading import Thread
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
import threading
from sqlalchemy import *
import collections
import os
import glob
import time
import pprint
import json

#logging.basicConfig(filename="snoopy.log",level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

class snoop(Thread):
    """
    This plugin handles 802.11 (WiFi) packets. Submodules are loaded from the mods80211 directory.
    Pass a value for the interface to listen on, default being mon0
    """
    @staticmethod
    def get_modules():
        
        moduleNames=["plugins.mods80211." + os.path.basename(f)[:-3] for f in glob.glob("./plugins/mods80211/*.py") if not os.path.basename(f).startswith('__')]
        return moduleNames
            
    @staticmethod
    def get_tables():
        tables=[]
        for m in snoop.get_modules():
            tmp=__import__(m,fromlist=['snarf']).snarf()
            tbls=tmp.get_tables()
            for tbl in tbls:
                tables.append(tbl)
        return tables

    def __init__(self,*args):

        self.iface=None
        if len(args)>0 and args[0] != None:
            self.iface=args[0][0]
        else:
            logging.error("No interface specified!")
        
        Thread.__init__(self)
        self.STOP_SNIFFING=False
        self.time=2
        self.db_buffer=collections.deque()      
        self.c=0

        self.modules=[]
        for m in snoop.get_modules():
            tmp=__import__(m,fromlist=['snarf']).snarf()
            self.modules.append(tmp)


        moduleNames=["plugins.client.mods80211." + os.path.basename(f)[:-3] for f in glob.glob("./plugins/client/mods80211/*.py") if not os.path.basename(f).startswith('__')]


    @staticmethod
    def get_parameter_list():
        return ["<wifi_interface> - interface to listen on. (e.g. -m c80211:mon0)"] #TODO: ,"<proximity_delta> - time between observataions to group proximity sessions (e.g. -m:c80211:mon0,60"]


        def get_ident_tables(self):
                """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return ['proximity_sessions']


    def stop(self):
        self.STOP_SNIFFING=True

    def run(self):

        if self.iface == None:
            logging.error("No interface specified for '%s' module, cannot run"%__name__)
        else:
            logging.debug("Starting sniffer plugin on interface '%s'"%self.iface)

            while self.STOP_SNIFFING==False:
                try:
                            sniff(store=0,iface=self.iface,prn=self.packeteer,stopperTimeout=1, stopper=self.stopperCheck)
                        except Exception,e:
                                logging.error("Scapy exception whilst sniffing. Will back off for 10 seconds, and try restart '%s' plugin"%__name__)
                                logging.error(e)
                    time.sleep(10)
#                               self.STOP_SNIFFING=True
        def stopperCheck(self):
        return self.STOP_SNIFFING

    def packeteer(self,p):
        # Give the packet to each module

        if ( p.haslayer(Dot11ProbeReq) ):
            mac=p.addr2
            ssid=p[Dot11Elt].info
            ssid=ssid.decode('utf-8','ignore')

#           self.f1.write(mac + "\n")
#           if ssid != '':
#               self.f2.write(ssid + "\n")

#           self.f1.flush()
#           self.f2.flush()

        for m in self.modules:
            m.proc_packet(p)

#       newtime=int(time.time())
#       if( newtime - self.time >= self.DATA_WRITE_FREQ ):
#           self.get_data()
#           self.time=newtime

    def get_data(self):

        data_to_return=[]
        for m in self.modules:          
            data=m.get_data()
            if data != None and len(data) >0:
                tblname=data[0]
                vals=data[1]
                data_to_return.append((tblname,vals))

        return data_to_return


def main():
    foo=snoop("mon0")


if __name__ == "__main__":

#   with launch_ipdb_on_exception():
    main()
