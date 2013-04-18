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
from scapy.all import sniff, Dot11Elt, Dot11ProbeReq
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

        # Process arguments passed to module
        self.iface = kwargs.get('iface',None)
        self.enable_monitor_mode = kwargs.get('mon',False)
        self.bfilter = kwargs.get('filter',"")

        Thread.__init__(self)
        self.setName('c80211')
        self.STOP_SNIFFING = False

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

    def is_ready(self):
        return self.ready_status

    def stop(self):
        self.STOP_SNIFFING = True

    def run(self):
        #if self.iface is None:
        #    logging.error("No interface specified for '%s' module, cannot run" % __name__)
        #else:
        #    logging.debug("Starting sniffer plugin on interface '%s'" % self.iface)

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
            except Exception:
                logging.exception(("Scapy exception whilst sniffing. "
                                   "Will back off for 10 seconds, "
                                   "and try restart '%s' plugin") % __name__)
                self.sniffErrors+=1
            if self.sniffErrors >3 :
                logging.error("Restarting module '%s' after 5 failed attempts" %__file__)
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
