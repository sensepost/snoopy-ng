# -*- coding: utf-8 -*-
from threading import Thread
import threading
from sqlalchemy import *
import logging

#logging.basicConfig(filename="snoopy.log",level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

class snoop(Thread):
	def __init__(self,*args):
		Thread.__init__(self)	
		self.RUN=True

		self.table=None		
		"""Make sure to define your table here. Ensure you have a sunc column"""
#		metadata=MetaData()
#		self.table=Table('sample_table',metadata,
#			Column('sample_row1', String(12), primary_key=True),
#			Column('sample_row2',Unicode, primary_key=True),
#			Column('sunc',Integer,default=0)
#			)


	def run(self):
		"""Operations for module go here"""

	def stop(self):
		self.RUN=False

	@staticmethod
	def get_parameter_list():
		return ["None"]

	def get_data(self):
                """Ensure data is returned in the form of a SQL row """
		return []

	def get_ident_tables(self):
		"""Return a list of tables that requrie identing - i.e. adding drone name and location"""
		return [self.table]

	@staticmethod
	def get_tables():
		return []


if __name__=="__main__":
	x=snoop()
	x.start()
