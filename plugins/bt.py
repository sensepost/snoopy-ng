# -*- coding: utf-8 -*-
from threading import Thread
import threading
from sqlalchemy import *
import time
from bluetooth import discover_devices
import logging

#logging.basicConfig(filename="snoopy.log",level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

class snoop(Thread):
    def __init__(self,*args):
        Thread.__init__(self)   
        self.devices={}
        self.RUN=True
        
        """Make sure to define your table here"""
        metadata=MetaData()
        self.table=Table('bluetooth',metadata,
            Column('mac', String(12), primary_key=True),
            Column('name',Unicode, primary_key=True),
            Column('sunc',Integer,default=0)
            )


    def run(self):
        logging.debug("Starting bluetooth module")
        while self.RUN:
            foundDevs = discover_devices(lookup_names=True) 
            for (addr, name) in foundDevs:
                name=name.decode('utf-8','ignore')
                if (addr,name) not in self.devices:
                    self.devices[(addr,name)]=0

            tmptimer=0
            while ( self.RUN==True and tmptimer<5 ):
                time.sleep(0.1)
                tmptimer+=0.1

    def stop(self):
        self.RUN=False

    @staticmethod
    def get_parameter_list():
        return ["None"]

    def get_data(self):
                """Ensure data is returned in the form of a SQL row """

                tmp=[]
                todel=[]
                for k,v in self.devices.iteritems():
                        if v == 0:
                                tmp.append( {"mac":k[0], "name":k[1]})
                                todel.append((k[0],k[1]))

                if len(todel) > 0:
                        for foo in todel:
                                mac,name=foo[0],foo[1]
                                self.devices[(mac,name)]=1
                        return [("bluetooth",tmp)]
        return []

    def get_ident_tables(self):
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return []
#       return ['bluetooth']

    def get_tables(self):
        return [self.table]


if __name__=="__main__":
    x=snoop()
    x.start()
