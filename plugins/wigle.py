#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlalchemy as sa
from threading import Thread


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(filename)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class Snoop(Thread):
    def __init__(self, *kwargs):
        Thread.__init__(self)
        self.RUN = True
        self.username=''
        self.password=''
        self.db='snoopy.db'

        # Process arguments passed to module
        self.username = kwargs.get('username','NoUserNameSupplied')
        self.password = kwargs.get('password','NoPasswordSupplied')
        self.db = kwargs.get('db',None)


    def run(self):
       # while self.RUN:
       pass


    def stop(self):
        self.RUN = False

    @staticmethod
    def get_parameter_list():
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
        return []


if __name__ == "__main__":
    Snoop().start()
