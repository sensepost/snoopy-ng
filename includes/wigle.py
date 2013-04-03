import time
from random import randint
import re
import sys
from collections import deque
import requests
from BeautifulSoup import BeautifulSoup
import pprint
import math
import socket
import sys
import logging
import os
import urllib2
import httplib2
import urllib
import json

class Wigle(object):

    def __init__(self):
        self.url = {'land':"https://wigle.net/", 'login': "https://wigle.net/gps/gps/main/login", 'query':"http://wigle.net/gps/gps/main/confirmquery/"}

    def login(self,user,passw):
        """Login to Wigle service"""
        self.user = user
        self.password = passw
        self.cookies = None

        logging.debug("[+] Logging into wigle with %s:%s via proxy '%s'" %(self.user,self.password))
        payload={'credential_0':self.user, 'credential_1':self.password}
        try:
            r = urllib2.Request(self.url['login'], payload)
        except Exception, e: #(requests.exceptions.ConnectionError,requests.exceptions.Timeout), e:
            print e
            return {'result':'fail','error':e}
        if( 'Please login' in r.text or 'auth' not in r.cookies):
            logging.debug("[-] Error logging in with credentials %s:%s. Thread returning." %(self.user,self.password))
            return {'result':'fail', 'error':'Unable to login to wigle'}
        else:
            logging.debug("[-] Successfully logged in with credentials %s:%s." %(self.user,self.password))
            self.cookies=dict(auth=r.cookies['auth'])
            return {'result':'success'}
