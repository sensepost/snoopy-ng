#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json
from flask import Flask, request, Response, abort
from functools import wraps
from sqlalchemy import create_engine, MetaData, Table, Column, String,\
                   select, and_, Integer
from collections import deque
from sqlalchemy.exc import *
import time
from datetime import datetime
from auth_handler import auth

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

path="/"
logging.debug("Loading webserver code")

app = Flask(__name__)
auth_ = auth()
server_data = deque(maxlen=100000)

def write_local_db(rawdata):
    """Write server db"""
    for entry in rawdata:
        tbl = entry['table']
        data = entry['data']
        if tbl not in metadata.tables.keys():
            logging.error("Error: Drone attempting to insert data into invalid table '%s'"%tbl)
            return False
        tbl=metadata.tables[tbl]
        try:
            tbl.insert().execute(data)
        except Exception,e:
             logging.exception(e)
             return False
    return True

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_admin_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not verify_admin(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not auth_.verify_account(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def unpack_data(request):
    if request.headers['Content-Type'] == 'application/json':
       try:
           return json.loads(request.data)
       except Exception,e:
           logging.error(e)

# For the collection of data
@app.route(path, methods=['POST'])
@requires_auth
def catch_data():
    try:
        jsdata = unpack_data(request)
        #Dirty hack for converting back to a datetime object. Should rather define via column name? e.g. dt_observation
        for d in jsdata['data']:
            for k,v in d.iteritems():
                try:
                    tmp=d[k]
                    d[k]=datetime.strptime(d[k],"%Y-%m-%d %H:%M:%S")
                except Exception, e:
                    pass
        #result = write_local_db(jsdata)
        server_data.append((jsdata['table'], jsdata['data']  ) )

    except Exception,e:
        logging.error("Unable to parse JSON from '%s'" % request)
        print jsdata
        logging.error(e)
        return '{"result":"failure", "reason":"Check server logs"}'
    else:
        return '{"result":"success", "reason":"None"}'

def poll_data():
        rtnData=[]
        while server_data:
            rtnData.append(server_data.popleft())
        if rtnData:
            return rtnData
        else:
            return []

def run_webserver(port=9001,ip="0.0.0.0"):
    #create_db_tables()
    app.run(host=ip, port=port)

if __name__ == "__main__":
    run_webserver()
