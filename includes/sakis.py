#!/usr/bin/env python
# -*- coding: utf-8 -*-
# glenn@sensepost.com
import subprocess
from threading import Thread
import time
import sys
import os
import logging

DN = open(os.devnull, 'w')
logging.basicConfig(format='%(message)s', level=logging.DEBUG)

scriptPath=os.path.dirname(os.path.realpath(__file__))
os.chdir(scriptPath)

class Sakis(Thread):
    """Uses the sakis3g binary to maintain a 3G connection. Supply APN"""
    def __init__(self,apn):
        self.apn=apn
        if not os.path.isfile("./sakis3g"):
            logging.error("Error: 'sakis3g' binary is not in '%s' directory" % scriptPath)
            sys.exit(-1)
        Thread.__init__(self)
        self.start()

    def run(self):
        logging.info("[+] Starting backround 3G connection maintainer.")
        logging.info("[-] Current status is '%s'" % self.status())
        while self.run:
            if self.status() != "Connected":
                logging.info("[+] Attempting to connect to 3G network '%s'" % self.apn)
                self.connect(self.apn)
                time.sleep(2)
                if self.status() == "Connected":
                    logging.info("[+] Successfully connected to '%s'" % self.apn)
            time.sleep(5)
    
    def stop(self):
        logging.info("[+] Stopping 3G connector. Will leave connection in its current state.")
        self.run = False

    @staticmethod
    def status():
        try:
            r=subprocess.call(["./sakis3g", "status"], stdout=DN, stderr=DN)
            if r == 0:
                return "Connected"
            elif r == 6:
                return "Disconnected"
            else:
                return "Unknown"
        except:
             return "Error"
    @staticmethod
    def disconnect():
        r=subprocess.call(["./sakis3g", "disconnect"], stdout=DN, stderr=DN)

    @staticmethod
    def get_apns():
        return "ToDo"

    @staticmethod
    def connect(apn):
        try:
            r=subprocess.call(["./sakis3g", "connect", "APN='%s'"%apn], stdout=DN, stderr=DN)
            return r
        except:
            return -1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Please supply APN (e.g. 'orange.fr'")
        sys.exit(-1)
    f=None
    try: 
        f=Sakis(sys.argv[1])
    except KeyboardInterrupt:
        f.stop()
