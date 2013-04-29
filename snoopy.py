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
    MODULE_START_GRACE_TIME = 60 #A module gets this time to indicate its ready, before moving to next module.

    def __init__(self, _modules, dbms="sqlite:///snoopy.db",
                 server="http://localhost:9001/", drone="unnamedDrone",
                 key=None, location="unknownLocation"):
        #moduleNames = ["plugins."+ x for x in moduleNames]
        #local data
        self.all_data = {}
        self.run = True
        self.server = server
        self.drone = drone
        self.location = location
        self.key = key
        self.run_id = ''.join(random.choice(string.ascii_uppercase + string.digits)
                              for x in range(10))
        #Database
        self.tables = {}
        try:
            self.db = create_engine(dbms)
            self.metadata = MetaData(self.db)
        except:
            logging.error("Badly formed dbms schema. See http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html for examples of valid schema")
            sys.exit(-1)
        self.ident_tables = []

        self._load_modules(_modules)

        try:
            self.go()
        except KeyboardInterrupt:
            print "Caught Ctrl+C! Shutting down..."
            self.stop()

    def _load_modules(self, modules_to_load):
        self.modules = []
        for mod in modules_to_load:
            mod_name = mod['name']
            mod_params = mod['params']
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


    def _load_modules_old(self, moduleNames):
#        self.modules = []
#        for mod in moduleNames:
#            mds = mod.split(":", 1)
#            mod = mds[0]
#            params = None
#            if len(mds) > 1:
#                params = mds[1].split(",")
          
        self.modules = []
        for mod in moduleNames.iteritems(): 

            m = __import__(mod, fromlist="Snoop").Snoop(params)
            mod_start_time = os.times()[4]    #Get a system clock indepdent timer
            m.start()
            logging.info("[+] Waiting for module '%s' to indicate it's ready" % mod)
            while not m.is_ready() and (os.times()[4] - mod_start_time) < self.MODULE_START_GRACE_TIME:
                time.sleep(2)
            if not m.is_ready():
                logging.info("Module '%s' ran out of time to indicate its ready state, moving on to next module." % mod)
            else:
                logging.info("Modules '%s' has indicated it's ready." % mod)

            self.modules.append(m)

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

    @staticmethod
    def get_plugins():
        """List available plugins without instantiating the object."""
        return [ os.path.basename(f)[:-3]
                        for f in glob.glob("./plugins/*.py")
                        if not os.path.basename(f).startswith('__') ]

    def go(self):
        #Proceed
        last_update = 0
        while self.run:
            self.get_data()
            self.write_local_db()
            now = time.time()
            if now - last_update > self.SYNC_FREQ:
                last_update = now
                if self.server != "local":
                    self.sync_to_server()
            time.sleep(1) #Delay between checking threads for new data

    def stop(self):
        self.run = False
        for m in self.modules:
            m.stop()

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
            try:
                if tbl in self.ident_tables:
                    for d in data:
                        d['drone'] = self.drone
                        d['location'] = self.location
                        d['run_id'] = self.run_id
                self.tables[tbl].insert().prefix_with("OR REPLACE").execute(data)
            except Exception, e:
                logging.debug("1. Exception ->'%s'<- whilst attempting to insert data:" %(str(e)) )
                logging.debug("2. Data was ->'%s'<-" %(str(data)) )
                logging.debug("3. Sleeping for 5 secs")
                time.sleep(5)
            else:
                #Clean up local datastore
                if self.all_data:
                    self.all_data = {}

    def sync_to_server(self):
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
                    data_to_upload.append({"table": table_name,
                                           "data": result_as_dict})
            else:
                logging.debug("Ignoring table %s (no 'sunc' column)"%table)

        if data_to_upload:
            data_to_upload = json.dumps(data_to_upload)
            sync_success = self.web_upload(data_to_upload)

            # If web sync was successful, mark local db as sunc
            if sync_success:
                logging.debug("Successfully sync'd %d rows of data :)" %
                              total_rows_to_upload)
                for table_name in self.tables: #self.metadata.sorted_tables:
                    table = self.tables[table_name]
                    if "sunc" in table.c:
                        upd = table.update(values={table.c.sunc:1})
                        upd.execute()
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
                logging.error("Unable to upload data to '%s' - '%s'"% (self.server,reason))
                return False
        except Exception, e:
            logging.error("Unable to upload data to '%s' - '%s'"% (self.server,e))
            logging.debug(e)
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
    print "Snoopy V0.2. glenn@sensepost.com\n"
    usage = """Usage: %prog [--client <http://sync_server:port> | --server <listen_port>] [--dbms <database>] [--module <module[:params]>] [<client options> | <server options>]"""
    parser = OptionParser(usage=usage)
    #Client options
    group_c = OptionGroup(parser, "Client Options")

    if os.geteuid() != 0:
        sys.exit("Please run me with root privilages")

    parser.add_option("-c", "--client", dest="sync_server", action="store", help="Run Snoopy client component, uploading data to specified SYNC_SERVER (http://host:port) (specifcy 'local' for local only capture).")
    group_c.add_option("-d", "--drone", dest="drone", action="store", help="Specify the name of your drone.")
    group_c.add_option("-k", "--key", dest="key", action="store", help="Specify key for drone name supplied.")
    group_c.add_option("-l", "--location", dest="location", action="store", help="Specify the location of your drone.")

    #parser.add_option("-", "--", dest="", action="store_true", help="")

    #Server options
    group_s = OptionGroup(parser, "Server Options")

    parser.add_option("-s", "--server", dest="server_port", type="int", action="store", help="Run Snoopy sync server component on specified port.")
    parser.add_option("-p", "--path", dest="server_path", action="store", default="/", help="Run Snoopy sync server component from web path (default '/')")
    group_s.add_option("-n", "--new_drone", dest="newdrone", action="store", help="Create a new drone account, supplying the name. Will output a key to be used by client.")
    group_s.add_option("-e", "--erase_drone", dest="deldrone", action="store", help="Delete a drone account by its name.")
    group_s.add_option("-a", "--list_drones", dest="listdrones", action="store_true", help="List all drone accounts.")

    #Common options
    parser.add_option("-b", "--dbms", dest="dbms", action="store", type="string", default="sqlite:///snoopy.db", help="Database to use, in SQL Alchemy format. [default: %default]")
    parser.add_option("-m", "--module", dest="module", action="append", help="Module to load. Pass parameters with colon. e.g '-m c80211:mon0,aggressive'. Use -i to list available modules and their paramters.")
    #parser.add_option("-p", "--parameters", dest="parameters", action="append", help="Optional module parameters, per module. Omit for default.")
    parser.add_option("-i", "--list", dest="list", action="store_true", help="List all available modules and exit.", default=False)

    parser.add_option_group(group_c)
    parser.add_option_group(group_s)

    options, args = parser.parse_args()

    moduleNames = Snoopy.get_plugins() #[os.path.basename(f)[:-3] for f in glob.glob("./plugins/client/*.py") if not os.path.basename(f).startswith('__')]
    if options.list:
        print "[+] Modules available:"
        for mod in moduleNames:
            tmp = mod
            mod = "plugins." + mod
            m = __import__(mod, fromlist="Snoop").Snoop
            param_list = m.get_parameter_list()
            print "\tName: \t%s" % tmp
            for p in param_list:
                print "\tParameter: \t%s" % p
            print "\n"
        sys.exit(0)
    if options.newdrone:
        print "[+] Creating new Snoopy server sync account"
        import includes.webserver
        key = includes.webserver.Webserver.manage_drone_account(options.newdrone,
                                                                "create",
                                                                options.dbms)
        print "[+] Key for '%s' is '%s'" % (options.newdrone, key)
        print "[+] Use this value in client mode to sync data to a remote server. e.g:"
        print ("    %s --client http://remote-server/ --drone %s --key %s "
               "--location <somelocation> -m <module01> -m <modules02>") % \
              (__file__, options.newdrone, key)
        sys.exit(0)
    elif options.deldrone:
        import includes.webserver
        print "[+] Deleting drone account '%s'" % options.deldrone
        includes.webserver.Webserver.manage_drone_account(options.deldrone,
                                                          "delete",
                                                          options.dbms)
        sys.exit(0)
    elif options.listdrones:
        import includes.webserver
        print "[+] Available drone accounts:"
        drones = includes.webserver.Webserver.manage_drone_account(1, "list",
                                                                   options.dbms)
        for d in drones:
            print "\t%s:%s" % (d[0], d[1])
        sys.exit(0)

    if (options.sync_server is not None and options.server_port is not None) or \
            (options.sync_server is None and options.server_port is None):
        logging.error("No options specified. Try -h for help.")
        sys.exit(-1)

    #Client mode
    if options.sync_server is not None:
        if options.drone is None or options.location is None :
            logging.error("You must specify drone name (-d) and drone location (-l)")
            sys.exit(-1)
        if options.sync_server == "local":
            logging.info("Capturing local only")
        else:
            if options.key is None:
                logging.error("You must specify a key when uploading data (-k)")
                sys.exit(-1)

        mods = options.module
        if options.module is None:
            #mods = moduleNames
            logging.error("Error: You must specify at least one module. Try -h for help")
            sys.exit(-1)
        #Check validity of mods
        for m in mods:
            if m.split(":", 1)[0] not in moduleNames:
                logging.error("Invalid module - '%s'. Use --list to list all available modules." % (m.split(':', 1)[0]))
                sys.exit(-1)
        logging.info("Starting Snoopy with modules: %s" % (str(mods)))

        newmods=[]
        for m in mods:
            mds = m.split(":", 1)
            name = mds[0]
            params = {}
            if len(mds) > 1:
                params = dict(a.split("=") for a in mds[1].split(","))        
            newmods.append({'name':'plugins.'+name, 'params':params})

        Snoopy(newmods, options.dbms, options.sync_server, options.drone,
               options.key, options.location)

    #Server mode
    else:
        logging.info ("[+] Starting Snoopy sync web server. "
               "Listening on port '%d' with sync web path '%s'" % \
              (options.server_port, options.server_path))
        import includes.webserver
        includes.webserver.Webserver(options.dbms,
                                     options.server_path, options.server_port)

if __name__ == "__main__":
    main()
