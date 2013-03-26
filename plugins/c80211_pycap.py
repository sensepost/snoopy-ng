# -*- coding: utf-8 -*-
import pcap,dpkt,binascii,sys
import logging
from sqlalchemy import *
from threading import Thread
import collections

import traceback
import time

"""SSID and Prox session calculator. Using pylibpcap"""
class snoop(Thread):

    def __init__(self,*args):
        Thread.__init__(self)
        self.RUN=True
                self.dict_device_ssids={}

        self.iface=None
                if len(args)>0 and args[0] != None:
                        self.iface=args[0][0]
                else:
                        logging.error("No interface specified!")
            self.iface="NoInterfaceSelected"
        self.p=None

        #Prox sess vars
        self.MOST_RECENT_TIME=0
        self.dict_current_proximity_sessions={}
        self.q_closed_proximity_sessions=collections.deque()
        self.DELTA_PROX=300                                     # Proximity session duration, before starting a new one

    def run(self):
        while self.RUN:
            try:
                    logging.debug("Starting pcapy WiFi module")
                self.p=pcap.pcapObject()
                self.p.open_live(self.iface, 1600, 0, 100)
                if ( self.p.datalink() != dpkt.pcap.DLT_IEEE802_11_RADIO ):
                    logging.error("Selected interface '%s' is not in monitor mode. Will wait 10 seconds and try again."%self.iface)
                    time.sleep(10)
                else:
                            while self.RUN:
                        self.p.dispatch(1, self.process_packet)
            except Exception,e:
                logging.error("Error occured trying to monitor '%s': '%s'. Will wait 10 seconds and try again."%(self.iface,e))
                time.sleep(10)  

    @staticmethod
        def get_parameter_list():
                return ["<wifi_interface> - interface to listen on. (e.g. -m c80211_pycap:mon0)"] #TODO: ,"<proximity_delta> - time between observataions to group proximity sessions (e.g. -m:c80211:mon0,60"]

    def stop(self):
        self.RUN=False      
        print "Stopping"

    def process_packet(self,pktlen, rawdata, timestamp):
        timestamp=int(timestamp)
        if not rawdata:
            return
        try:        
            tap = dpkt.radiotap.Radiotap(rawdata)
            signal_ssi=-(256-tap.ant_sig.db)     #Calculate signal strength
            t_len=binascii.hexlify(rawdata[2:3])     #t_len field indicates the entire length of the radiotap data, including the radiotap header.
            t_len=int(t_len,16)          #Convert to decimal

            # This fails with 1.5% of captures in testing. Cause: unknown.
            wlan = dpkt.ieee80211.IEEE80211(rawdata[t_len:])
            if wlan.type == 0 and wlan.subtype == 4: # Indicates a probe request
                ssid = wlan.ies[0].info
                ssid=ssid.decode('utf-8','ignore')  #Correct way to handle UTF?
                mac=binascii.hexlify(wlan.mgmt.src)
            
                if ssid != "":
                    self.do_ssid(mac,ssid,timestamp)
                self.do_prox(mac,timestamp)

        except:
            pass
#           print traceback.format_exc()
            
    
    def do_ssid(self,mac,ssid,ts):  
        if (mac,ssid) not in self.dict_device_ssids:
            self.dict_device_ssids[(mac,ssid)]=0

    
    def do_prox(self,mac,t):
        self.MOST_RECENT_TIME=int(t)
        # New
                if mac not in self.dict_current_proximity_sessions:
                        self.dict_current_proximity_sessions[mac]=[t,t,1,0]
                else:   
                        #Check if expired
                        self.dict_current_proximity_sessions[mac][2]+=1         #num_probes counter
                        first_obs=self.dict_current_proximity_sessions[mac][0]
                        last_obs=self.dict_current_proximity_sessions[mac][1]
                        num_probes=self.dict_current_proximity_sessions[mac][2]
                        if(t - last_obs >= self.DELTA_PROX):
                                self.q_closed_proximity_sessions.append((mac,first_obs,t,num_probes))
                                del(self.dict_current_proximity_sessions[mac])
                        else:   
                                self.dict_current_proximity_sessions[mac][1]=t
                                self.dict_current_proximity_sessions[mac][3]=0 #Mark as require db sync 


        @staticmethod
        def get_tables():
                """Make sure to define your table here"""
                metadata=MetaData()
                table_ssids=Table('ssids',metadata,
                        Column('device_mac', String(12), primary_key=True),
                        Column('ssid',Unicode, primary_key=True),
                        Column('sunc',Integer,default=0)
                        )


        table_prox=Table('proximity_sessions',metadata,
                        Column('mac', String(12), primary_key=True),
                        Column('first_obs',Integer, primary_key=True),
                        Column('last_obs',Integer),
                        Column('num_probes',Integer),
                        Column('sunc',Integer,default=0)
                        )

                return [table_ssids,table_prox]

        def get_ident_tables(self):
                """Return a list of tables that requrie identing - i.e. adding drone name and location"""
                return ['proximity_sessions']



        def get_prox_data(self):
                """Ensure data is returned in the form (tableName,[colname:data,colname:data]) """

                # First check if expired, if so, move to closed
                # Use the most recent packet received as a timestamp. This may be more useful than taking
                #  the system time as we can parse pcaps.
                todel=[]
                data=[]
                for mac,v in self.dict_current_proximity_sessions.iteritems():
                        first_obs=v[0]
                        last_obs=v[1]
                        num_probes=v[2]
                        t=self.MOST_RECENT_TIME
                        if(t - last_obs >= self.DELTA_PROX):
                                self.q_closed_proximity_sessions.append((mac,first_obs,t,num_probes))
                                todel.append(mac)
                for mac in todel:
                        del(self.dict_current_proximity_sessions[mac])
                #1. Open Prox Sessions
                tmp=[]
                for mac,v in self.dict_current_proximity_sessions.iteritems():
                        first_obs,last_obs,num_probes=v[0],v[1],v[2]
                        if v[3] == 0:
                                tmp.append({"mac":mac,"first_obs":first_obs,"last_obs":last_obs,"num_probes":num_probes})
                                #tmp.append((k,v[0],v[1],v[2]))
                #2. Closed Prox Sessions
                tmp2=[]
                for i in range(len(self.q_closed_proximity_sessions)):
                        mac,first_obs,last_obs,num_probes=self.q_closed_proximity_sessions.popleft()
                        tmp2.append( {"mac":mac,"first_obs":first_obs,"last_obs":last_obs,"num_probes":num_probes} )
                if( len(tmp+tmp2) > 0 ):
                        #data.append(   (table,columns,tmp+tmp2)    )
                        #Set flag to indicate data has been fetched:
                        for i in tmp:
                                mac=i['mac']
                                self.dict_current_proximity_sessions[mac][3]=1

                        #return None
                        return ("proximity_sessions",tmp+tmp2)
        return []

    

        def get_ssid_data(self):
                """Ensure data is returned in the form of a SQL row """

                tmp=[]
                todel=[]
                for k,v in self.dict_device_ssids.iteritems():
                        if v == 0:
                                tmp.append( {"device_mac":k[0], "ssid":k[1]} )
                                todel.append((k[0],k[1]))

                if len(todel) > 0:
                        for foo in todel:
                                mac,ssid=foo[0],foo[1]
                                self.dict_device_ssids[(mac,ssid)]=1
                        return ("ssids",tmp)
        return[]
        
    def get_data(self):
        return [self.get_ssid_data() ,self.get_prox_data()]


