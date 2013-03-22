#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import glob
import logging
import os
import scapy
import time
from threading import Thread

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)


class Snoop(Thread):
    """
    This plugin handles 802.11 (WiFi) packets. Submodules are loaded from the
    mods80211 directory.  Pass a value for the interface to listen on, default
    being mon0.
    """

    def __init__(self, *args):
        self.iface = None
        if args and args[0] is not None:
            self.iface = args[0][0]
        else:
            logging.error("No interface specified!")

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
        return ["<wifi_interface> - interface to listen on. (e.g. -m c80211:mon0)"]

    def get_ident_tables(self):
        """Return a list of tables that requrie identing - i.e. adding drone
            name and location."""
        return ['proximity_sessions']

    def stop(self):
        self.STOP_SNIFFING = True

    def run(self):
        if self.iface is None:
            logging.error("No interface specified for '%s' module, cannot run" % __name__)
        else:
            logging.debug("Starting sniffer plugin on interface '%s'" % self.iface)

        while self.STOP_SNIFFING == False:
            try:
                scapy.sniff(store=0, iface=self.iface, prn=self.packeteer,
                            stopperTimeout=1, stopper=self.stopperCheck)
            except Exception:
                logging.exception(("Scapy exception whilst sniffing. "
                                   "Will back off for 10 seconds, "
                                   "and try restart '%s' plugin") % __name__)
            time.sleep(10)
        #self.STOP_SNIFFING=True

    def stopperCheck(self):
        return self.STOP_SNIFFING

    def packeteer(self, p):
        # Give the packet to each module

        if p.haslayer(scapy.Dot11ProbeReq):
            ssid = p[scapy.Dot11Elt].info
            ssid = ssid.decode('utf-8', 'ignore')

            #mac = p.addr2
            #self.f1.write(mac + "\n")
            #if ssid != '':
            #    self.f2.write(ssid + "\n")

            #self.f1.flush()
            #self.f2.flush()

        for m in self.modules:
            m.proc_packet(p)

        #newtime = int(time.time())
        #if newtime - self.time >= self.DATA_WRITE_FREQ:
        #    self.get_data()
        #    self.time = newtime

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
    Snoop("mon0")
