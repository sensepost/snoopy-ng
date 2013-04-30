#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from threading import Thread
from sqlalchemy import MetaData, Table, Column, String, Integer

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class Snoop(Thread):
    def __init__(self, **kwargs):
        # Process arguments passed to module
        Thread.__init__(self)

    def run(self):
        """Operations for module go here."""
        pass

    def is_ready(self):
        """Indicates the module is ready, and loading of next module may commence."""
        return False

    def stop(self):
        """Perform operations required to stop module and return"""
        pass

    @staticmethod
    def get_parameter_list():
        """List of paramters that can be passed to the module, for user help output."""
        return ["None"]

    def get_data(self):
        """Ensure data is returned in the form of a SQL row."""
        return []

    @staticmethod
    def get_ident_tables():
        """Return a list of tables that requrie identing - i.e. adding drone name and location"""
        return []

    @staticmethod
    def get_tables():
        """Return the table definitions for this module."""
        # Make sure to define your table here. Ensure you have a 'sunc' column:
        # table = Table('sample_table',Metadata(),
        #                      Column('sample_row1', String(12), primary_key=True),
        #                      Column('sample_row2', Unicode, primary_key=True),
        #                      Column('sunc', Integer, default=0))
        # return table
        return []


if __name__ == "__main__":
    Snoop().start()
