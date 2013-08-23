#!/usr/bin/python
# -*- coding: utf-8 -*-
# glenn@sensepost.com_
# snoopy_ng // 2013
# By using this code you agree to abide by the supplied LICENSE.txt

import sys
import os
from MaltegoTransform import *
import logging
from datetime import datetime
from sqlalchemy import create_engine, MetaData, select, and_
from transformCommon import *
logging.basicConfig(level=logging.DEBUG,filename='/tmp/maltego_logs.txt',format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

def main():
#    print "Content-type: xml\n\n";
#    MaltegoXML_in = sys.stdin.read()
#    logging.debug(MaltegoXML_in)
#    if MaltegoXML_in <> '':
#     m = MaltegoMsg(MaltegoXML_in)

    #Custom query per transform, but apply filter with and_(*filters) from transformCommon.
    #db.echo=True
    filters.append(proxs.c.mac == vends.c.mac)
    s = select([proxs.c.mac,vends.c.vendor, vends.c.vendorLong], and_(*filters))
    #s = select([proxs.c.mac,vends.c.vendor, vends.c.vendorLong], and_(proxs.c.mac == vends.c.mac, proxs.c.num_probes>1 ) ).distinct()
    r = db.execute(s)
    results = r.fetchall()
    TRX = MaltegoTransform()

    for mac,vendor,vendorLong in results:
        NewEnt=TRX.addEntity("snoopy.Client", vendor)
        NewEnt.addAdditionalFields("mac","mac address", "strict",mac)
        NewEnt.addAdditionalFields("vendor","vendor", "strict", vendor)
        NewEnt.addAdditionalFields("vendorLong","vendorLong", "strict", vendorLong)
    TRX.returnOutput()		

main()
#me = MaltegoTransform()
#me.addEntity("maltego.Phrase","hello bob")
#me.returnOutput()                
