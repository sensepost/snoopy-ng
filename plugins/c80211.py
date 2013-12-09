#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import glob
import logging
import os
import time
from threading import Thread
import includes.monitor_mode as mm
#import includes.LogManager
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import sniff, Dot11Elt, Dot11ProbeReq, rdpcap, Scapy_Exception
from collections import deque
import time
from plugins.mods80211.prefilter.prefilter import prefilter
import sys
#logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

class Snoop(Thread):
    """
    This plugin handles 802.11 (WiFi) packets. Submodules are loaded from the
    mods80211 directory.  Pass a value for the interface to listen on, default
    being mon0.
    """

    def __init__(self, **kwargs):
        self.sniffErrors = 0    # Number of times scapy has failed
        self.ready_status = False
        self.packet_queue = deque(maxlen=1000000)
        self.packet_buffer_size=10000 #Number of packets to pop to each module from the queue

        # Process arguments passed to module
        self.iface = kwargs.get('iface',None)
        self.enable_monitor_mode = kwargs.get('mon',"False")
        self.bfilter = kwargs.get('filter',"")
        self.hash_macs = kwargs.get('hash',"False")
        self.pcap = kwargs.get('pcap')

        if self.enable_monitor_mode == "False":
            self.enable_monitor_mode = False
        else:
            self.enable_monitor_mode = True

        Thread.__init__(self)
        self.setName('c80211')
        self.STOP_SNIFFING = False

        self.modules = []
        for m in Snoop.get_modules():
            #self.modules.append(__import__(m, fromlist=['Snarf']).Snarf(hash_macs=self.hash_macs))
            self.modules.append(__import__(m, fromlist=['Snarf']).Snarf(**kwargs))

    @staticmethod
    def get_modules():
        return [ "plugins.mods80211." + os.path.basename(f)[:-3]
                 for f in glob.glob("./plugins/mods80211/*.py")
                 if not os.path.basename(f).startswith('__') ]

    @staticmethod
    def get_tables():
        tables = []
        for m in Snoop.get_modules():
            tbls = __import__(m, fromlist=['Snarf']).Snarf()
            tables.extend(tbls.get_tables())
        return tables

    @staticmethod
    def get_parameter_list():
        #TODO: "<proximity_delta> - time between observataions to group proximity sessions (e.g. -m:c80211:mon0,60")
        sub_plugs = ""
        for m in Snoop.get_modules():
            sub_plug = __import__(m, fromlist=['Snarf']).Snarf
            desc =  sub_plug.__doc__
            name = m.split(".")[-1]
            sub_plugs += "\n\t\t\t *%s - %s" % (name,desc)

        info = {"info" : "This plugin intercepts and processes network traffic. A series of sub-plugins exists within the 'mods' subfolder. Existing sub-plugins are:%s\n"%sub_plugs,
                "parameter_list" : [("iface=<dev>", "interface to listen on. e.g. -m c80211:iface=wlan3"),
                                    ("mon=[True|False]","First enable monitor mode on <iface>. e.g. -m c80211:iface=wlan3,mon=True. If no <iface> specified, will find first appropriate one."),
                                    ]
                }
        return info

    def is_ready(self):
        return self.ready_status

    def stop(self):
        self.STOP_SNIFFING = True

    def parse_pcap(self):
        logging.info("Reading in '%s' capture file (slow)..." % self.pcap)
        try:
            data = rdpcap(self.pcap)
        except Exception, e:
            logging.error("Unable to read in '%s' capture file: '%s'" % (self.pcap, e))
            logging.error("Did you create '%s' with tcpdump?" % self.pcap)
            self.stop()
            sys.exit(-1)
        else:
            logging.info("Done reading in '%s'. Processsing..." % self.pcap)
            for p in data:
                self.packeteer(p)
            logging.info("Finished.... I won't re-read this file, so you may want to exit and restart if you populate it again.")


    def run(self):
        if self.pcap:
            self.ready_status = True
            self.parse_pcap()
        else:

            shownMessage = False
            while not self.STOP_SNIFFING:
                if self.enable_monitor_mode:
                        self.iface=mm.enable_monitor_mode(self.iface)
                        if not self.iface:
                                if not shownMessage:
                                    logging.error("No suitable monitor interface available. Will check every 5 seconds, but not display this message again.")
                                    shownMessage = True
                                time.sleep(5)
                if not self.iface and self.enable_monitor_mode:
                    continue
                if not self.iface:
                    logging.info("No interface specified. Will sniff *all* interfaces.")
                else:
                    logging.info("Starting sniffing on interface '%s'"%self.iface)
                try:
                    self.ready_status = True
                    shownMessage = False
                    sniff(store=0, iface=self.iface, prn=self.packeteer, filter=self.bfilter,
                          stopperTimeout=1, stopper=self.stopperCheck)
                except Exception, e:
                    logging.error(("Scapy exception whilst sniffing. "
                                       "Will back off for 5 seconds, "
                                       "and try restart '%s' plugin") % __name__)
                    logging.error(e)
                    self.sniffErrors+=1
                if self.sniffErrors >3 :
                    logging.error("Restarting module '%s' after 5 failed attempts" %__file__)
                time.sleep(5)

    def stopperCheck(self):
        return self.STOP_SNIFFING

    def packeteer(self, p):
        """In the interest of thread safety, we now do this sequentially."""
        # Give the packet to each module
        #for m in self.modules:
        #    m.proc_packet(p)
        self.packet_queue.append(p)

    def get_data(self):
        #First we pop N packets from the packet queue and pass them to each module
        for i in range(self.packet_buffer_size):
            try:
                packet = self.packet_queue.popleft()
                if prefilter(packet):
                    for m in self.modules:
                        m.proc_packet(packet)
            except IndexError:
                break

        time.sleep(0.2) #Give each module some time to process the packets

        #Then we query each module for any data they may have constructed from the
        #   received packets
        data_to_return = []
        for m in self.modules:
            data = m.get_data()
            if data:
                tblname = data[0]
                vals = data[1]
                data_to_return.append((tblname, vals))
        return data_to_return


if __name__ == "__main__":
    #with launch_ipdb_on_exception():
    Snoop()
