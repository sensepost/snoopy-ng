#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json
import glob
import os
import random
import string
import sys
from flask import Flask, request, Response, abort
from functools import wraps
from sqlalchemy import create_engine, MetaData, Table, Column, String,\
                       select, and_, Integer
from collections import deque


logging.basicConfig(level=logging.DEBUG, filename='snoopy_server.log',
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class Webserver(object):
    def __init__(self, dbms="sqlite:///snoopy.db", path="/", srv_port=9001):
        #Database
        try:
            self.db = create_engine(dbms)
            self.metadata = MetaData(self.db)
        except:
            logging.error ("Badly formed dbms schema. See http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html for examples of valid schema")
            sys.exit(-1)

        self.tables = {}

        logging.debug("Writing server database: %s" % dbms)
        logging.debug("Listening on port: %d" % srv_port)
        logging.debug("Sync URL path: %s" % path)

        #Load db tables from client modules
        ident_tables = []
        moduleNames = [ "plugins." + os.path.basename(f)[:-3]
                        for f in glob.glob("./plugins/*.py")
                        if not os.path.basename(f).startswith('__') \
                            and not os.path.basename(f).startswith(__file__) ]
        logging.info("Server loaded modules: %s" % str(moduleNames))
        logging.debug("Server loading tables from plugins:%s" % str(moduleNames))
        self.tbls = []
        tbl_drone=Table('drones', MetaData(),
                        Column('drone', String(40), primary_key=True),
                        Column('key', String(40)))
        self.tbls.append(tbl_drone)

        for mod in moduleNames:
            m = __import__(mod, fromlist="Snoop").Snoop#()
            for ident in m.get_ident_tables():
                if ident is not None:
                    ident_tables.append(ident)
            
            tmptables = m.get_tables()
            for t in tmptables:
                self.tbls.append(t)

        for tbl in self.tbls:
            tbl.metadata = self.metadata
            if tbl.name in ident_tables:
                tbl.append_column( Column('drone',String(length=20)) )
                tbl.append_column( Column('location', String(length=60)) )
                tbl.append_column( Column('run_id', String(length=11)) )
            self.tables[tbl.name] = tbl
            if not self.db.dialect.has_table(self.db.connect(), tbl.name):
                 tbl.create()

        logging.debug("Starting webserver")
        self.run_webserver(path,srv_port)

    @staticmethod
    def manage_drone_account(drone, operation, dbms):
        db = create_engine(dbms)
        metadata = MetaData(db)

        drone_table = Table('drones', metadata,
                            Column('drone', String(40), primary_key=True),
                            Column('key', String(40)))

        if not db.dialect.has_table(db.connect(), drone_table.name):
            drone_table.create()

        if operation == "create":
            try:
                key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                              for x in range(15))
                drone_table.insert().prefix_with("OR REPLACE")\
                    .execute(drone=drone, key=key)
            except Exception:
                logging.exception("Exception whilst attemptign to add drone")
            else:
                return key
        elif operation == "delete":
            drone_table.delete().execute(drone=drone)
            return True
        elif operation == "list":
            return(drone_table.select().execute().fetchall())
        else:
            logging.error("Bad operation '%s' passed to manage_drone_account" %
                          operation)
            return False

    def write_local_db(self, rawdata):
        """Write server db"""
        for entry in rawdata:
            tbl = entry['table']
            data = entry['data']
            if tbl not in self.tables:
                logging.error("Error: Drone attempting to insert data into invalid table '%s'"%tbl)
                return False
            try:
                self.tables[tbl].insert().prefix_with("OR REPLACE").execute(data)
            except Exception:
                logging.exception('Error:')
            else:
               return True

    def verify_admin(self, user, pwd):
        if user == "potato" and pwd == "fl0atb0at":
            return True

    def verify_account(self, _drone, _key):
        try:
            drone_table=self.tables['drones']
            s = select([drone_table],
                       and_(drone_table.c.drone==_drone, drone_table.c.key==_key))
            result = self.db.execute(s).fetchone()

            if result:
                logging.debug("Auth granted for %s" % _drone)
                return True
            else:
                logging.debug("Access denied for %s" % _drone)
                return False
        except Exceptioni, e:
            logging.exception('Error: %s' %str(e))
            return False

    def authenticate(self):
        """Sends a 401 response that enables basic auth"""
        return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

    def requires_admin_auth(self,f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not self.verify_admin(auth.username, auth.password):
                return self.authenticate()
            return f(*args, **kwargs)
        return decorated

    
    def requires_auth(self,f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not self.verify_account(auth.username, auth.password):
                return self.authenticate()
            return f(*args, **kwargs)
        return decorated
    
    def unpack_data(self, request):
        if request.headers['Content-Type'] == 'application/json':
           try:
               return json.loads(request.data)
           except Exception,e:
               logging.error(e)

    #Perhaps make this a module?
    def run_webserver(self, path, srv_port):
        app = Flask(__name__)

        #Command shell variables
        self.pendingCommands = {}
        self.newResponses = {}

        @app.route('/cmd/droneResponse')
        @self.requires_auth
        def drone_response():
            drone = auth = request.authorization.username
            if 'command' not in request.args or 'output' not in request.args:
                abort(400)
            else:
                command, output = request.args['command'], request.args['output']
                if drone not in self.newResponses:
                    self.newResponses[drone] = deque([(command,output)])
                else:
                    self.newResponses[drone].append((command,output))
                logging.info(self.newResponses)
                return "Thank you, kind sir."
        
        @app.route('/cmd/droneQuery')
        @self.requires_auth
        def drone_query():
            _drone = auth = request.authorization.username
            if _drone in self.pendingCommands and self.pendingCommands[_drone]:
                return self.pendingCommands[_drone].popleft()
            else:
                return ""
        
        @app.route('/cmd/serverGetResponse')
        @self.requires_admin_auth
        def server_get_response():
            if 'drone' not in request.args:
                return "Please specify 'drone' parameter"
            else:
                drone = request.args['drone']
                if drone in self.newResponses and self.newResponses[drone]:
                    command, output = self.newResponses[drone].popleft()
                    resp = "[%s] %s\n%s" %(drone, command, output)
                    return Response(resp, mimetype="text/plain")
                else:
                    return ""
                
        @app.route('/cmd/serverAddCommand')
        @self.requires_admin_auth
        def server_add_command():
            if 'command' not in request.args or 'drone' not in request.args:
                return "Please specify 'command' and 'drone' parameters"
            else:
                command, drone = request.args['command'], request.args['drone']
                if drone not in self.pendingCommands:
                    self.pendingCommands[drone] = deque([command])
                else:
                    self.pendingCommands[drone].append(command)
                logging.info(self.pendingCommands)
                return "Sending command '%s' to '%s'" % (command, drone)
        

        # For the collection of data
        @app.route(path, methods=['POST'])
        @self.requires_auth
        def catch_data():
            jsdata = self.unpack_data(request)
            if jsdata:
                result = self.write_local_db(jsdata)

                if result:
                    return '{"result":"success", "reason":"None"}'
                else:
                    return '{"result":"failure", "reason":"Check server logs"}'

        #app.debug=True
        app.run(host="0.0.0.0",port=srv_port)


if __name__ == "__main__":
    Webserver().start()
