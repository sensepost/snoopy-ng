#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import logging
import re
from sqlalchemy import MetaData, Table, Column, String, Integer

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import Dot11ProbeReq

class Snarf():
    """Proximity session calculator"""

    DELTA_PROX = 300
    """Proximity session duration, before starting a new one."""

    def __init__(self):
        self.current_proximity_sessions = {}
        self.closed_proximity_sessions = collections.deque()
        self.MOST_RECENT_TIME = 0

    @staticmethod
    def get_tables():
        """Make sure to define your table here"""
        table = Table('proximity_sessions', MetaData(),
                      Column('mac', String(12), primary_key=True),
                      Column('first_obs', Integer, primary_key=True),
                      Column('last_obs', Integer),
                      Column('num_probes', Integer),
                      Column('sunc', Integer, default=0))
        return [table]

    def proc_packet(self,p):
        self.MOST_RECENT_TIME = int(p.time)
        if not p.haslayer(Dot11ProbeReq):
            return
        mac = re.sub(':', '', p.addr2)
        t = int(p.time)
        # New
        if mac not in self.current_proximity_sessions:
            self.current_proximity_sessions[mac] = [t, t, 1, 0]
        else:
            #Check if expired
            self.current_proximity_sessions[mac][2] += 1 #num_probes counter
            first_obs = self.current_proximity_sessions[mac][0]
            last_obs = self.current_proximity_sessions[mac][1]
            num_probes = self.current_proximity_sessions[mac][2]
            if (t - last_obs) >= self.DELTA_PROX:
                self.closed_proximity_sessions.append((mac, first_obs, t, num_probes))
                del(self.current_proximity_sessions[mac])
            else:
                self.current_proximity_sessions[mac][1] = t
                self.current_proximity_sessions[mac][3] = 0 #Mark as require db sync

    def get_data(self):
        # First check if expired, if so, move to closed
        # Use the most recent packet received as a timestamp. This may be more
        # useful than taking the system time as we can parse pcaps.
        todel = []
        for mac, v in self.current_proximity_sessions.iteritems():
            first_obs, last_obs, num_probes = v[:3]
            t = self.MOST_RECENT_TIME
            if (t - last_obs) >= self.DELTA_PROX:
                self.closed_proximity_sessions.append((mac, first_obs, t, num_probes))
                todel.append(mac)
        for mac in todel:
            del self.current_proximity_sessions[mac]

        #1. Open Prox Sessions
        open_sess = []
        for mac, v in self.current_proximity_sessions.iteritems():
            first_obs, last_obs, num_probes = v[:3]
            if v[3] == 0:
                open_sess.append({"mac": mac,
                                  "first_obs": first_obs, "last_obs": last_obs,
                                  "num_probes": num_probes})
        #2. Closed Prox Sessions
        closed_sess=[]
        for i in range(len(self.closed_proximity_sessions)):
            mac, first_obs, last_obs, num_probes = self.closed_proximity_sessions.popleft()
            closed_sess.append({"mac": mac,
                                "first_obs": first_obs, "last_obs": last_obs,
                                "num_probes": num_probes})

        if open_sess and closed_sess:
            #Set flag to indicate data has been fetched:
            for i in open_sess:
                mac = i['mac']
                self.current_proximity_sessions[mac][3] = 1

        if len( open_sess + closed_sess ) > 0:
            return ("proximity_sessions", open_sess+closed_sess)
