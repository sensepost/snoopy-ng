# -*- coding: utf-8 -*-
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
from sqlalchemy import *

"""SSID processor"""
class snarf():

	def __init__(self):	
		self.dict_device_ssids={}

	@staticmethod
	def get_tables():
		"""Make sure to define your table here"""
		metadata=MetaData()
		table=Table('ssids',metadata,
			Column('device_mac', String(12), primary_key=True),
			Column('ssid',Unicode, primary_key=True),
			Column('sunc',Integer,default=0)
			)
		return [table]
	
	def proc_packet(self,p):
		if ( p.haslayer(Dot11ProbeReq) and p[Dot11Elt].info != '' ):
                        mac=re.sub(':','',p.addr2)
                        ssid=p[Dot11Elt].info
			ssid=ssid.decode('utf-8','ignore')
                        if (mac,ssid) not in self.dict_device_ssids:
                                self.dict_device_ssids[(mac,ssid)]=0

	def get_data(self):
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
