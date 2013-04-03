#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import glob
import logging
import os
import time
from threading import Thread
import includes.monitor_mode as mm

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import sniff, Dot11Elt, Dot11ProbeReq
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')


class Snoop(Thread):
    """
    This plugin handles 802.11 (WiFi) packets. Submodules are loaded from the
    mods80211 directory.  Pass a value for the interface to listen on, default
    being mon0.
    """

    def __init__(self, *args):
        self.iface = None
        self.enable_monitor_mode = False
        self.bfilter = ''
	self.error = False	# Set to true to signal that thread has failed. Parent may then terminate and restart
        self.sniffErrors = 0    # Number of times scapy has failed
        if args and args[0] is not None:
            try:
                pargs=dict(a.split("=") for a in args[0])# for a in args[0][0].split(","))
                if 'iface' in pargs:
                    self.iface = pargs['iface']
                if 'mon' in pargs and pargs['mon'].lower()=="true":
                    self.enable_monitor_mode = True
                if 'filter' in pargs:
                    self.bfilter = pargs['filter']
            except:
                logging.error("Bad arguments passed to module")
            #self.iface = args[0][0]

        Thread.__init__(self)
        self.STOP_SNIFFING = False
        self.time = 2
        self.db_buffer = collections.deque()

        self.modules = []
        for m in Snoop.get_modules():
            self.modules.append(__import__(m, fromlist=['Snarf']).Snarf())

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
        return ["iface=<dev> - interface to listen on. (e.g. -m c80211:iface=wlan3)","mon=[True|False] - Enable monitor mode on <dev> (e.g. -m c80211:iface=wlan3,mon=True","filter=<bpf> - Filter to apply. (e.g. -mc c80211:filter='foobar'"]

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone
            name and location."""
        return ['proximity_sessions']

    def stop(self):
        self.STOP_SNIFFING = True

    def run(self):
        #if self.iface is None:
        #    logging.error("No interface specified for '%s' module, cannot run" % __name__)
        #else:
        #    logging.debug("Starting sniffer plugin on interface '%s'" % self.iface)

        while not self.STOP_SNIFFING:
    
            if self.enable_monitor_mode:
                    self.iface=mm.enable_monitor_mode(self.iface)
                    if not self.iface:
                            print "[!] No suitable monitor interface available. Will look again in 5 seconds."
                            logging.error("No suitable monitor interface available. Will look again in 5 seconds")
                            time.sleep(5)
            if not self.iface and self.enable_monitor_mode:
                continue
            if not self.iface:
                print "[W] Warning, no interface specified. Will sniff *all* interfaces."
            else:
                print "[+] Starting sniffing on interface '%s'"%self.iface
            try:
                sniff(store=0, iface=self.iface, prn=self.packeteer, filter=self.bfilter,
                      stopperTimeout=1, stopper=self.stopperCheck)
            except Exception:
                logging.exception(("Scapy exception whilst sniffing. "
                                   "Will back off for 10 seconds, "
                                   "and try restart '%s' plugin") % __name__)
                self.sniffErrors+=1
            if self.sniffErrors >3 :
                logging.error("Restarting module after 5 failed attempts")
                print "[!] Restarting module '%' after 5 errors"%__file__
            else:
                time.sleep(2)

    def stopperCheck(self):
        return self.STOP_SNIFFING

    def packeteer(self, p):
        # Give the packet to each module
        for m in self.modules:
            m.proc_packet(p)

    def get_data(self):
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
