#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlalchemy as sa
from threading import Thread
from includes.run_prog import run_program
import time
logging.basicConfig(level=logging.DEBUG)

class Snoop(Thread):
    def __init__(self, *kwargs):
        Thread.__init__(self)
        self.ready = False
        self.RUN = True

    def run(self):
        sleeps = 600
        while self.RUN:
            if sleeps >= 600:
                self.set_time()    #Check every ten mins
                sleeps = 0
            time.sleep(1)
            sleeps+=1

    def set_time(self):
        clock_attempts=5
        success = run_program('ntpdate ntp.ubuntu.com')
        while not success and clock_attempts > 0:
            logging.info("Failed to set system clock. Will try %d more times before giving up" %clock_attempts)
            clock_attempts-=1
            time.sleep(15)
            success = run_program('ntpdate',['ntp.ubuntu.com'])
        logging.info("System clock is currently %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        self.ready = True

    def is_ready(self):
        """Indicates the module is ready, and loading of next module may commence."""
        return self.ready

    def stop(self):
        """Perform operations required to stop module and return"""
        self.RUN = False

    @staticmethod
    def get_parameter_list():
        """List of paramters that can be passed to the module, for user help output."""
        info = {"info" : "Sets the system time via NTP every ten minutes.",
                "parameter_list" : None
                }
        return info

    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        return []

    @staticmethod
    def get_tables():
        """Return the table definitions for this module."""
        return []


if __name__ == "__main__":
    Snoop().start()
