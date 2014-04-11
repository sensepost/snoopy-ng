#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, MetaData, Table, Column, String,\
                   select, and_, Integer
from sqlalchemy.exc import *
import os
import sys
import logging
import random
import string

path=os.path.dirname(os.path.realpath(__file__))

class auth:
    """Handle authentication"""
    def __init__(self,dbms="sqlite:///%s/snoopy_creds.db" % path):
        self.db = create_engine(dbms)
        self.metadata = MetaData(self.db)
        self.metadata.reflect()

        self.drone_tbl_def = Table('drones', MetaData(),
                            Column('drone', String(40), primary_key=True),
                            Column('key', String(40)))

    def manage_drone_account(self,drone, operation):
        #if not self.db.dialect.has_table(self.db.connect(), 'drones'):
        if 'drones' not in self.metadata.tables.keys():
            self.db.create(self.drone_tbl_def )
        self.metadata.reflect()
        drone_table = self.metadata.tables['drones']
    
        if operation == "create":
            try:
                key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                              for x in range(15))
                drone_table.insert().execute(drone=drone, key=key)
                logging.info("Created new drone '%s'" % drone)
            except IntegrityError:
                logging.error("Drone '%s' already exists!" %drone) #REPLACE INTO will actually just replace it
            except Exception:
                logging.exception("Exception whilst attempting to add drone")
            else:
                return key
        elif operation == "delete":
            result = self.db.execute("DELETE FROM drones WHERE drone='{0}'".format(drone))
            if result.rowcount == 0:
                logging.warning("No such account. Ignoring")
            #drone_table.delete().execute(drone=drone)
            return True
        elif operation == "list":
            return(drone_table.select().execute().fetchall())
        else:
            logging.error("Bad operation '%s' passed to manage_drone_account" %
                          operation)
            return False
    
    def verify_account(self,_drone, _key):
        try:
            drone_table=self.metadata.tables['drones']
            s = select([drone_table],
                       and_(drone_table.c.drone==_drone, drone_table.c.key==_key))
            result = self.db.execute(s).fetchone()
    
            if result:
                #logging.debug("Auth granted for %s" % _drone)
                return True
            else:
                logging.debug("Access denied for %s" % _drone)
                return False
        except Exception, e:
            logging.error('Unable to query access control database. Have you run snoopy_auth to create an account?')
            return False
    
    def verify_admin(self,user, pwd):
        if user == "serval" and pwd == "tanzaniaMountainClimbing13":
            return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c","--create", help="Create a new drone account")
    parser.add_argument("-d","--delete", help="Delete an existing drone account")
    parser.add_argument("-l","--list", help="List all drones and keys", action="store_true")
    args = parser.parse_args()

    if len(sys.argv) < 2:
        print "[!] No options supplied. Try --help."
    else:

        auth_ = auth()
        if args.create:
            print "[+] Creating new Snoopy server sync account"
            key = auth_.manage_drone_account(args.create, "create")
            if key:
                print "[+] Key for '%s' is '%s'" % (args.create, key)
                print "[+] Use this value in client mode to sync data to a remote server."
        elif args.delete:
            if auth_.manage_drone_account(args.delete, "delete"):
                print "[+] Deleting '%s'" % args.delete
        elif args.list:
            print "[+] Available drone accounts:"
            drones = auth_.manage_drone_account("foo", "list")
            for d in drones:
                print "\t%s:%s" % (d[0], d[1])

