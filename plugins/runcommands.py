#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from sqlalchemy import MetaData, Table, Column, String, Integer
from threading import Thread
import base64
import time
import urllib2
import json
from collections import deque
from includes.run_prog import run_program

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class Snoop(Thread):
    def __init__(self, **kwargs):

        self.server = "http://192.168.11.46:9001/" + "cmd_check"
        self.drone = 'beagle2'
        self.key = '0FUVVGNDTUMHYQ1'
        self.RUN = True
        self.command_queue = deque()
        Thread.__init__(self)

    def run(self):
        """Operations for module go here."""

        while self.RUN:
            self.fetch_command()
            time.sleep(5)

    def fetch_command(self):
        """Check if any new commands need to be executed"""
        base64string = base64.encodestring('%s:%s' % (self.drone, self.key)).replace('\n', '')
        headers = {'content-type': 'application/json',
                   'Authorization':'Basic %s' % base64string}        
   
        try:
            req = urllib2.Request(self.server, headers=headers)
            response = urllib2.urlopen(req)

            if response:
                result = json.loads(response.read())
                # A bug exists where after receving a new command, it's received again
                # but with a value of 'None'. Debug it with this:
                logging.debug("Going to req command '%s'" % result)        
                if result['cmd'] != None:
                    outcome = run_program(result['cmd'])
                    result['result'] = outcome
                    self.command_queue.append(result)
        except ValueError:
            """Blank response, no new commands"""
            pass
#        except Exception, e:
#            logging.error(e)



    def is_ready(self):
        """Indicates the module is ready, and loading of next module may commence."""
        return True 

    def stop(self):
        """Perform operations required to stop module and return"""
        self.RUN = False
        pass

    @staticmethod
    def get_parameter_list():
        """List of paramters that can be passed to the module, for user help output."""
        return ["None"]

    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        if self.command_queue:
       	    return [("commands", [self.command_queue.pop()])]
        else:
            return []

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return []

    @staticmethod
    def get_tables():
        """Return the table definitions for this module."""

        tbl_commands=Table('commands', MetaData(),
                        Column('id', Integer, primary_key=True),
                        Column('drone', String(40)),
                        Column('command', String(200)),
                        Column('has_run', Integer, default=0),
                        Column('result', String(1000)),
                        Column('sunc', Integer, default=0))
        return [tbl_commands]



if __name__ == "__main__":
    Snoop().start()
