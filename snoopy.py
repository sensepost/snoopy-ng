#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Glenn Wilkinson 2013
import glob
import os
import logging
import time
import json
import sys
#import requests # Python 2.7.3rc3 on Maemo cannot use this module
import urllib2   # In the meantime, we shall use urllib2
from optparse import OptionParser, OptionGroup
from sqlalchemy import create_engine, MetaData, Column, String
import base64
#Server
import string
import random
#CommandShell
from includes.command_shell import CommandShell
from includes.common import *
import includes.common as common
import datetime

#Set path
snoopyPath=os.path.dirname(os.path.realpath(__file__))
os.chdir(snoopyPath)

#Logging
logging.addLevelName(logging.INFO,"+")
logging.addLevelName(logging.ERROR,"!")
logging.addLevelName(logging.DEBUG,"D")

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='snoopy.log',
                    filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
logging.getLogger('').addHandler(console)


class Snoopy():
    SYNC_FREQ = 5 #Sync every 5 seconds
    SYNC_LIMIT = 200 #How many rows to upload at a time
    MODULE_START_GRACE_TIME = 60 #A module gets this time to indicate its ready, before moving to next module.

    def __init__(self, _modules, dbms="sqlite:///snoopy.db",
                 server="http://localhost:9001/", drone="unnamedDrone",
                 key=None, location="unknownLocation", cmdShell=True, flush_local_data_after_sync=True):
        #local data
        self.doCmdShell=False
        if cmdShell:
            logging.debug("Running cmdshell!")
            self.doCmdShell=True
        self.all_data = {}
        self.run = True
        self.server = server
        self.drone = drone
        self.location = location
        self.key = key
        self.run_id = ''.join(random.choice(string.ascii_uppercase + string.digits)
                              for x in range(10))
        self.flush_local_data_after_sync = flush_local_data_after_sync
        #Command Shell
        if self.doCmdShell:
            self.cmdShell = CommandShell(self.server, self.drone, self.key)

        #Database
        self.tables = {}
        try:
            self.db = create_engine(dbms)
            self.metadata = MetaData(self.db)
        except Exception, e:
            logging.error("Unable to create DB: '%s'.\nPossibly a badly formed dbms schema? See http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html for examples of valid schema" %str(e))
            sys.exit(-1)
        self.ident_tables = []

        self._load_modules(_modules)

        try:
            self.go()
        except KeyboardInterrupt:
            print "Caught Ctrl+C! Saving data and shutting down..."
            self.stop()

    def _load_modules(self, modules_to_load):
        self.modules = []
        for mod in modules_to_load:
            mod_name = mod['name']
            mod_params = mod['params']
            mod_params['dbms'] = self.db
            mod_params['drone'] = self.drone
            mod_params['location'] = self.location
            mod_params['run_id'] = self.run_id
            m = __import__(mod_name, fromlist="Snoop").Snoop(**mod_params)
            self.modules.append(m)

            logging.debug("Creating/checking tables for %s" % mod_name)
            for ident in m.get_ident_tables():
                if ident is not None:
                    self.ident_tables.append(ident)
            tbls = m.get_tables()
            for tbl in tbls:
                tbl.metadata = self.metadata
                if tbl.name in self.ident_tables:
                    tbl.append_column( Column('drone', String(length=20)) )
                    tbl.append_column( Column('location', String(length=60)) )
                    tbl.append_column( Column('run_id', String(length=11)) )

                self.tables[tbl.name] = tbl
                if not self.db.dialect.has_table(self.db.connect(), tbl.name):
                    tbl.create()

        #Start modules
            m.start()
            mod_start_time = os.times()[4]    #Get a system clock indepdent timer
            logging.info("Waiting for module '%s' to indicate it's ready" % mod_name)
            while not m.is_ready() and (os.times()[4] - mod_start_time) < self.MODULE_START_GRACE_TIME:
                time.sleep(2)
            if not m.is_ready():
                logging.info("Module '%s' ran out of time to indicate its ready state, moving on to next module." % mod_name)
            else:
                logging.info("Module '%s' has indicated it's ready." % mod_name)

        logging.info("Done loading modules, running...")

    def go(self):
        if self.server != "local" and self.doCmdShell:
            self.cmdShell.start() #Start command shell
        last_update = 0
        while self.run:
            self.get_data()
            self.write_local_db()
            #now = time.time() #Unsafe when ntp is changing time
            now = int(os.times()[4])
            if now - last_update > self.SYNC_FREQ:
                last_update = now
                if self.server != "local":
                    self.sync_to_server()
            time.sleep(1) #Delay between checking threads for new data

    def stop(self):
        self.run = False
        if self.server != "local" and self.doCmdShell:
            self.cmdShell.stop()
        for m in self.modules:
            m.stop()
        self.write_local_db()
        if self.server != "local":
            self.sync_to_server()

    def get_data(self):
        """Fetch data from all plugins"""
        for m in self.modules:
            multidata = m.get_data()
            for rawdata in multidata:
                if rawdata is not None and rawdata:
                    tbl, data = rawdata
                    self.all_data.setdefault(tbl, []).extend(data)

    def write_local_db(self):
        """Write local sqlite db"""
        for tbl, data in self.all_data.iteritems():
            try: #WTF is this? Fix it.
                if tbl in self.ident_tables:
                    for d in data:
                        if 'drone' not in d: #Hack to avoid server module overwriting these values
                            d['drone'] = self.drone
                            d['location'] = self.location
                            d['run_id'] = self.run_id
                #tbl.insert().execute(data)
                self.tables[tbl].insert().execute(data)
                #self.tables[tbl].insert().prefix_with("OR REPLACE").execute(data)
            except Exception, e:
                logging.debug("1. Exception ->'%s'<- whilst attempting to insert data:" %(str(e)) )
                logging.debug("2. Data was ->'%s'<-" %(str(data)) )
                logging.debug("3. Sleeping for 5 secs")
                time.sleep(5)
            else:
                #Clean up local datastore
                if self.all_data:
                    self.all_data = {}

    def chunker(self, seq, size):
        return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))

    def sync_to_server(self):
        """Sync tables that have the 'sunc' column available"""

        for table_name in self.tables:
            table = self.tables[table_name]
            if "sunc" not in table.c:
                logging.debug("Not syncing table '%s' - no 'sunc' column" % table_name)
                continue
            query = table.select(table.c.sunc == 0)
            ex = query.execute()
            results = ex.fetchall()
            sync_success = True
            for data in self.chunker(results, self.SYNC_LIMIT):
                result_as_dict = [dict(e) for e in data]
                for result in result_as_dict:
                    for k,v in result.iteritems():
                        if isinstance(v,datetime.datetime):
                            result[k] = str(v)
                data_to_upload = {"table": table_name,
                                           "data": result_as_dict}
                data_to_upload =  json.dumps(data_to_upload)
                sync_result = self.web_upload(data_to_upload)
                if not sync_result:
                    logging.error("Unable to upload %d rows from table '%s'. Moving to next table (check logs for details). " % (len(data), table_name))
                    break
                else:
                    if self.flush_local_data_after_sync:
                        table.delete().execute()
                    else:
                        table.update(values={table.c.sunc:1}).execute()


    def sync_to_server_OLD(self):
        """Sync tables that have the 'sunc' column available"""
        data_to_upload = [] #JSON list
        total_rows_to_upload = 0
        for table_name in self.tables: #self.metadata.sorted_tables:
            table = self.tables[table_name]
            if "sunc" in table.c:
                query = table.select(table.c.sunc == 0)
                ex = query.execute()
                results = ex.fetchall()
                if results:
                    total_rows_to_upload += len(results)
                    result_as_dict = [dict(e) for e in results]
                    for result in result_as_dict:
                        for k,v in result.iteritems():
                            if isinstance(v,datetime.datetime):
                                result[k] = str(v) #e.g. for datetime.datetime
                    data_to_upload.append({"table": table_name,
                                           "data": result_as_dict})
            else:
                logging.debug("Ignoring table %s (no 'sunc' column)"%table)

        if data_to_upload:
            sync_success = True
            for data in chunker(data_to_upload, SYNC_LIMIT):
                data = json.dumps(data)
                sync_result = self.web_upload(data)
                if not sync_result:
                    sync_success = False

            # If web sync was successful, mark local db as sunc
            if sync_success:
                for table_name in self.tables: #self.metadata.sorted_tables:
                    table = self.tables[table_name]
                    upd = table.update(values={table.c.sunc:1})
                    upd.execute()
                    if "sunc" in table.c and self.flush_local_data_after_sync:
                            #logging.debug("Flushing local data storage")
                            #self.db.execute("DELETE FROM {0}".format(table_name))
                            numdel = table.delete().execute()
            else:
                logging.debug("Error attempting to upload %d rows of data :(" %
                              total_rows_to_upload)

    def web_upload(self, json_data):
        base64string = base64.encodestring('%s:%s' % (self.drone, self.key)).replace('\n', '')
        headers = {'content-type': 'application/json',
                   'Z-Auth': self.key, 'Z-Drone': self.drone, 'Authorization':'Basic %s' % base64string}

        # urllib2, until Maemo urllib3 fixed
        try:
            req = urllib2.Request(self.server, json_data, headers)
            response = urllib2.urlopen(req)
            result = json.loads(response.read())
            if result['result'] == "success":
                #logging.debug("Successfully uploaded data")
                return True
            else:
                reason = result['reason']
                logging.debug("Unable to upload data to '%s' - '%s'"% (self.server,reason))
                return False
        except Exception, e:
            logging.debug("Unable to upload data to '%s' -  Exception:'%s'"% (self.server,e))
            return False


        ### urllib3
        # Has serious issues with Python 2.7.3rc4
        #headers = {'content-type': 'application/json'}
        #response = requests.post(self.server, data=json_data, headers=headers)
        #result = json.loads(response.text)['result']
        #try:
        #    if result == "success":
        #        logging.debug("Successfully uploaded")
        #        return True
        #    else:
        #        return False

        #except Exception, e:
        #    logging.debug("Exception whilst attempting to upload data:")
        #    logging.debug(e)
        #    return False

def main():
    message = """
 ___  _  _  _____  _____  ____  _  _
/ __)( \( )(  _  )(  _  )(  _ \( \/ )
\__ \ )  (  )(_)(  )(_)(  )___/ \  /
(___/(_)\_)(_____)(_____)(__)   (__)
Version: 2.0
Code: glenn@sensepost.com
"""
    print message
    usage = """Usage: %prog [--server <http|xbee://sync_server:[port]> ] [--dbms <database>] [--module <module[:params]>]\nSee the upstart scripts for advice on auto starting on boot."""
    parser = OptionParser(usage=usage)

    if os.geteuid() != 0:
        logging.warning("Running without root privilages. Some things may not work.")

    parser.add_option("-s", "--server", dest="sync_server", action="store", help="Upload data to specified SYNC_SERVER (http://host:port) (Ommitting will save data locally).", default="local")
    parser.add_option("-d", "--drone", dest="drone", action="store", help="Specify the name of your drone.")
    parser.add_option("-k", "--key", dest="key", action="store", help="Specify key for drone name supplied.")
    parser.add_option("-l", "--location", dest="location", action="store", help="Specify the location of your drone.")
    parser.add_option("-r", "--shell", dest="cmd_shell", action="store_true", help="Run command shell for remote administration of drone.")
    parser.add_option("-f", "--flush", dest="flush", action="store_true", help="Flush local database after syncronizing with remote server. Default is to not flush.", default=False)

    parser.add_option("-b", "--dbms", dest="dbms", action="store", type="string", default="sqlite:///snoopy.db", help="Database to use, in SQL Alchemy format. [default: %default]")
    parser.add_option("-m", "--plugin", dest="plugin", action="append", help="Plugin to load. Pass parameters with colon. e.g '-m c80211:mon0,aggressive'. Use -i to list available plugins  and their paramters.")
    parser.add_option("-i", "--list", dest="list", action="store_true", help="List all available plugins and exit.", default=False)

    options, args = parser.parse_args()

    plugins = common.get_plugins()
    if options.list:
        print "[+] Plugins available:"
        for plug in plugins:
            plugin_info = plug.get_parameter_list()
            info, param_list = plugin_info.get('info'), plugin_info.get('parameter_list')
            name = str(plug).split(".")[1]
            print "\tName:\t\t%s" %name
            print "\tInfo:\t\t%s" %info
            if param_list:
                for p in param_list:
                    print "\tParameter: \t%s" %p[0]
                    print "\t\t\t%s" % p[1]
            print "\n"
        sys.exit(0)

    if options.plugin is None:
        logging.error("Error: You must specify at least one plugin. Try -h for help")
        sys.exit(-1)

    if (options.drone is None or options.location is None) and not ( len(options.plugin) == 1 and options.plugin[0].split(":")[0] == "server" ) :
        logging.error("You must specify drone name (-d) and drone location (-l). Does not apply if only running server plugin.")
        sys.exit(-1)
    if options.key is None and options.sync_server != "local":
        logging.error("You must specify a key when uploading data (-k)")
        sys.exit(-1)

    #Check validity of plugins
    for m in options.plugin:
        if m.split(":", 1)[0] not in common.get_plugin_names():
            logging.error("Invalid plugin - '%s'. Use --list to list all available plugins." % (m.split(':', 1)[0]))
            sys.exit(-1)
    logging.info("Starting Snoopy with plugins: %s" % (str(options.plugin)))

    newplugs=[]
    for m in options.plugin:
        mds = m.split(":", 1)
        name = mds[0]
        params = {}
        if len(mds) > 1:
            params = dict(a.split("=") for a in mds[1].split(","))
        newplugs.append({'name':'plugins.'+name, 'params':params})
    if options.sync_server == "local":
        logging.info("Capturing local only. Saving to '%s'" % options.dbms)
    Snoopy(newplugs, options.dbms, options.sync_server, options.drone,
           options.key, options.location, options.cmd_shell, options.flush)

if __name__ == "__main__":
    main()
