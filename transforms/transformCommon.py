from MaltegoTransform import *
from datetime import datetime
from sqlalchemy import create_engine, MetaData, select, and_
import logging
import re
from dateutil import parser
import os
logging.basicConfig(level=logging.DEBUG,filename='/tmp/maltego_logs.txt',format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

if not os.path.isdir("/etc/transforms"):
    print "ERROR: '/etc/tranforms' symlink doesn't exist"
    exit(-1)

f = open("/etc/transforms/db_path.conf")
dbms = f.readline().strip()

try:
    db = create_engine(dbms)
#db.echo = True
    metadata = MetaData(db)
    metadata.reflect()
except Exception,e:
    print "ERROR: Unable to communicate with DB specified in /etc/transforms/db_path.txt ('%s'). Error was '%s'" % str(e)
    exit(-1)

TRX = MaltegoTransform()
logging.debug(sys.argv)
TRX.parseArguments(sys.argv)

drone = TRX.getVar("properties.drone")
if TRX.getVar("drone"):
    drone = TRX.getVar("drone")

location = TRX.getVar("properties.dronelocation")
if TRX.getVar("location"):
    location = TRX.getVar("location")

start_time = TRX.getVar("properties.start_time", "2000-01-01 00:00:00.0")
if TRX.getVar("start_time"):
    start_time = TRX.getVar("start_time", "2000-01-01 00:00:00.0")

end_time = TRX.getVar("properties.end_time", "2037-01-01 00:00:00.0")
if TRX.getVar("end_time"):
    end_time = TRX.getVar("end_time", "2037-01-01 00:00:00.0")

mac = TRX.getVar("properties.mac")
if TRX.getVar("mac"):
    mac = TRX.getVar("mac")

ssid = TRX.getVar("properties.ssid")
if TRX.getVar("ssid"):
    ssid = TRX.getVar("ssid")   #Manually overide

domain = TRX.getVar("fqdn")


observation = TRX.getVar("properties.observation")

st_obj = parser.parse(start_time)
et_obj = parser.parse(end_time)

try:
    proxs = metadata.tables['proximity_sessions']
    vends = metadata.tables['vendors']
    ssids = metadata.tables['ssids']
    wigle = metadata.tables['wigle']
    sess  = metadata.tables['sessions'] 
    cookies = metadata.tables['cookies']
    leases = metadata.tables['dhcp_leases']
    sslstrip = metadata.tables['sslstrip']
    wpa = metadata.tables['wpa_handshakes']
except Exception, e:
    print "ERROR: Unable to query tables from supplied db (%s)" % dbms
    exit(-1)

filters = []
s = select([proxs], and_(*filters))
#filters.append(proxs.c.num_probes>1)

#logging.debug(filters)

if proxs is not None:
    filters.append(proxs.c.run_id == sess.c.runn_id)

if start_time is not None:
    filters.append(proxs.c.first_obs >= st_obj)

if end_time is not None:
    filters.append(proxs.c.last_obs <= et_obj)

if drone is not None:
    filters.append(sess.c.drone == drone)

if location is not None:
    filters.append(sess.c.location == location)

if mac is not None:
    filters.append(proxs.c.mac == mac)

if ssid is not None:
    filters.append(ssids.c.ssid == ssid)
