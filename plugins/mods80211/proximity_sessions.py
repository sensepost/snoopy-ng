# -*- coding: utf-8 -*-
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
from sqlalchemy import *
import collections

"""Proximity session calculator"""
class snarf():

	def __init__(self):	
		self.dict_current_proximity_sessions={}
                self.q_closed_proximity_sessions=collections.deque()
                self.DELTA_PROX=300 					# Proximity session duration, before starting a new one
                self.MOST_RECENT_TIME=0

	@staticmethod
	def get_tables():
		"""Make sure to define your table here"""
		metadata=MetaData()
		table=Table('proximity_sessions',metadata,
			Column('mac', String(12), primary_key=True),
			Column('first_obs',Integer, primary_key=True),
			Column('last_obs',Integer),
			Column('num_probes',Integer),
			Column('sunc',Integer,default=0)
			)
		return [table]
	
	def proc_packet(self,p):
		self.MOST_RECENT_TIME=int(p.time)
		if ( p.haslayer(Dot11ProbeReq) ):
                        mac=re.sub(':','',p.addr2)
                        t=int(p.time)
                        # New
                        if mac not in self.dict_current_proximity_sessions:
                                self.dict_current_proximity_sessions[mac]=[t,t,1,0]
                        else:   
                                #Check if expired
                                self.dict_current_proximity_sessions[mac][2]+=1		#num_probes counter
                                first_obs=self.dict_current_proximity_sessions[mac][0]
                                last_obs=self.dict_current_proximity_sessions[mac][1]
                                num_probes=self.dict_current_proximity_sessions[mac][2]
                                if(t - last_obs >= self.DELTA_PROX):
                                        self.q_closed_proximity_sessions.append((mac,first_obs,t,num_probes))
                                        del(self.dict_current_proximity_sessions[mac])
                                else:   
                                        self.dict_current_proximity_sessions[mac][1]=t
                                        self.dict_current_proximity_sessions[mac][3]=0 #Mark as require db sync 

	def get_data(self):
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

		

