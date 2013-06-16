#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlalchemy as sa
from threading import Thread
import time
#logging.basicConfig(level=logging.DEBUG)

class Snoop(Thread):
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.RUN = True
        self.last_heartbeat = 0
        self.heartbeat_freq = 60 # Beat every n seconds
        self.drone = kwargs.get('drone',"no_drone_name_supplied")

    def run(self):
        while self.RUN:
            time.sleep(2) #Nothing to do here
    def is_ready(self):
        """Indicates the module is ready, and loading of next module may commence."""
        return True

    def stop(self):
        """Perform operations required to stop module and return"""
        self.RUN = False

    @staticmethod
    def get_parameter_list():
        """List of paramters that can be passed to the module, for user help output."""
        return ["None"]

    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        now = int(os.times()[4])
        if now > self.last_heartbeat + self.heartbeat_freq:
            logging.debug("Heartbeat")
            self.last_heartbeat = now
            return [('heartbeat',[{'drone':self.drone,'timestamp':now}])]
        else:
            return []

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return []

    @staticmethod
    def get_tables():
        """Return the table definitions for this module."""
        # Make sure to define your table here. Ensure you have a 'sunc' column:
        metadata = sa.MetaData()
        table = sa.Table('heartbeat',metadata,
                              sa.Column('drone', sa.String(length=20)),
                              sa.Column('timestamp', sa.Integer, primary_key=True, autoincrement=False),
                              sa.Column('sunc', sa.Integer, default=0))
        return [table]


if __name__ == "__main__":
    Snoop().start()
