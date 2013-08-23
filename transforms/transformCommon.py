from MaltegoTransform import *
from datetime import datetime
from sqlalchemy import create_engine, MetaData, select, and_


dbms="sqlite:////root/snoopy_ng/snoopy.db"

db = create_engine(dbms)
#db.echo = True
metadata = MetaData(db)
metadata.reflect()

TRX = MaltegoTransform()
TRX = MaltegoTransform()
TRX.parseArguments(sys.argv)

drone = TRX.getVar("drone")
location = TRX.getVar("location")
start_time = TRX.getVar("start_time", "2000-01-01 00:00:00.0")
end_time = TRX.getVar("end_time", "2037-01-01 00:00:00.0")
mac = TRX.getVar("mac")
ssid = TRX.getVar("ssid")

st_obj = datetime.strptime(start_time,"%Y-%m-%d %H:%M:%S.%f")
et_obj = datetime.strptime(end_time,"%Y-%m-%d %H:%M:%S.%f")

proxs = metadata.tables['proximity_sessions']
vends = metadata.tables['vendors']
ssids = metadata.tables['ssids']
vends = metadata.tables['vendors']

filters = []
s = select([proxs], and_(*filters))
filters.append(proxs.c.num_probes>1)

if start_time is not None:
    filters.append(proxs.c.first_obs >= st_obj)
if end_time is not None:
    filters.append(proxs.c.last_obs <= et_obj)
if drone is not None:
    filters.append(proxs.c.drone == drone)
if location is not None:
    filters.append(proxs.c.location == location)
if mac is not None:
    filters.append(proxs.c.mac == mac)
if ssid is not None:
    filters.append(ssids.c.ssid == ssid)
