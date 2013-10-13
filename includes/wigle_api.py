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
import sys
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.ERROR)

url = {'land':"https://wigle.net/", 'login': "https://wigle.net/gps/gps/main/login", 'query':"http://wigle.net/gps/gps/main/confirmquery/"}

class Wigle(object):

    def __init__(self,user,passw,email,proxy=''):
        self.user = user
        self.password = passw
        self.proxies = {"http":proxy,"https":proxy}
        self.cookies = None
        self.email = email

        if not self.user or not self.password:
            logging.error("Please supply Wigle credentials!")
            sys.exit()

        if not self.email:
            logging.error("Please supply email address to Wigle for OpenStreetView lookups! Exiting")
            sys.exit()

    def login(self):
        """Login to Wigle service, and set cookies"""
        logging.debug("[+] Logging into wigle with %s:%s via proxy '%s'" %(self.user,self.password,self.proxies))
        payload={'credential_0':self.user, 'credential_1':self.password}
        try:
            r = requests.post(url['login'],data=payload,proxies=self.proxies,timeout=10)
        except Exception, requests.exceptions.ConnectionError:
            logging.error('error: Unable to connect to %s' %url['login'])
            return False
        else: 
            if( 'Please login' in r.text or 'auth' not in r.cookies):
                logging.debug("Error logging in with credentials %s:%s." %(self.user,self.password))
                return False
                #return {'result':'fail', 'error':'Unable to login to wigle'}
            else:
                logging.debug("Successfully logged in with credentials %s:%s." %(self.user,self.password))
                cookies=dict(auth=r.cookies['auth'])
                self.cookies = cookies
                return True

    def lookupSSID(self,ssid):
        """Lookup the co-ordinates (Wigle) and address (OpenStreetMaps) of an SSID. Provide a Wigle cookie"""
        if not self.cookies:
            logging.debug("Cookies not set - have you successfully logged in?")
            return {'error':'Cookie not set - have you succuessfully logged in?'}
        payload={'longrange1': '', 'longrange2': '', 'latrange1': '', 'latrange2':'', 'statecode': '', 'Query': '', 'addresscode': '', 'ssid': ssid.replace("_","\_"), 'lastupdt': '', 'netid': '', 'zipcode':'','variance': ''}
        try:
            r = requests.post(url['query'],data=payload,proxies=self.proxies,cookies=self.cookies,timeout=10)
            if( r.status_code == 200 and r.text):
                if('too many queries' in r.text):
                    logging.debug("User %s has been shunned" %(self.user))
                    return {'error':'User "%s" has been shunned' %self.user}
                elif('An Error has occurred:' in r.text):
                    logging.debug("An error occured whilst looking up '%s' with Wigle account '%s'" % (ssid,self.user))
                    return {'error':'Text response contained "An Error has occurred"'}
                elif('Showing stations' in r.text):
                    locations=self._fetch_locations(r.text,ssid)
                    #Lookup street address
                    if (locations != None and locations[0]['overflow'] == 0):
                        for l in locations:
                            l.update(self._getAddress(l['lat'],l['long']))
                    return locations
                else:
                    logging.debug("Unknown error occured whilst looking up '%s' with Wigle account '%s'" % (ssid,self.user))
                    return {'error':'Unknown error occured'}
            else:
                logging.debug("Bad status - %s" %r.status_code)
                return {'error':'Bad HTTP status - %s'%r.status_code}
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout), e:
            logging.debug("Exception. Unable to retrieve SSID '%s' - '%s'" %(ssid, str(e)))
            return {'error':e}

    def _fetch_locations(self,text,ssid):
        """Parse Wigle page to extract GPS co-ordinates"""
        soup=BeautifulSoup(text)
        results=soup.findAll("tr", {"class" : "search"})
        locations=[]
        overflow=0
        if (len(results)>99 ):
            overflow=1
        for line in results:
            try:
                row=line.findAll('td')
                if( row[2].string.lower() == ssid.lower()):
                    locations.append({'ssid':ssid,'mac':row[1].string, 'last_seen':row[9].string, 'last_update':row[15].string, 'lat':float(row[12].string), 'long':float(row[13].string),'overflow':overflow})
            except Exception:
                pass
        # Sort by last_update
        sorted=False
        while not sorted:
            sorted=True
            for i in range(0,len(locations)-1):
                if( int(locations[i]['last_update']) < int(locations[i+1]['last_update'])):
                    sorted=False
                    locations[i],locations[i+1] = locations[i+1],locations[i]
        # Remove duplicates within proximity of each other, keeping the most recent
        # TODO: Update this to find the great circle average
        remove_distance=5000 #5 kilometres
        tD={}
        for i in range(0,len(locations)-1):
            for j in range(i+1,len(locations)):
                dist=self._haversine(float(locations[i]['lat']),float(locations[i]['long']),float(locations[j]['lat']),float(locations[j]['long']))
                if (dist < remove_distance):
                    #logging.debug(" %d and %d are %d metres apart, thus, DELETION! :P" % (j,dist))
                    tD[j]=1
        tmp=[]
        for i in range(0,len(locations)):
            if (i not in tD):
                tmp.append(locations[i])
        locations=tmp
        if( len(locations) == 0):
            locations.append({'ssid':ssid,'overflow':-1}) #No results, just return the ssid
        return locations        # Return list of locations

    def _haversine(self, lat1, lon1, lat2, lon2):
        """Calculate distance between points on a sphere"""
        R = 6372.8 # In kilometers
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)

        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.sin(dLon / 2) * math.sin(dLon / 2) * math.cos(lat1) * math.cos(lat2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c * 1000.0 # In metres

    def _getAddress(self,gps_lat,gps_long):
        """Get street address from GPS coordinates"""
        lookup_url = "http://nominatim.openstreetmap.org/reverse?zoom=18&addressdetails=1&format=json&email=%s&lat=%s&lon=%s" %(self.email,gps_lat,gps_long)
        req = requests.get(lookup_url)
        if req.status_code == 200 and 'json' in req.headers['content-type']:
            #addj = json.loads(req.text.encode('UTF8'))
            addj = json.loads(req.text.encode('utf-8'))
            longaddress = addj.get('display_name', '')
            compound_address = addj.get('address', {})
            city = compound_address.get('city', '')
            country = compound_address.get('country', '')
            country_code = compound_address.get('country_code', '')
            county = compound_address.get('county', '')
            postcode = compound_address.get('postcode', '')
            housenumber = compound_address.get('house_number', '')
            road = compound_address.get('road', '')
            state = compound_address.get('state', '')
            suburb = compound_address.get('suburb', '')
            shortaddress = "%s %s, %s" %(housenumber, road, city)
            shortaddress = shortaddress.strip()

        return {'longaddress':longaddress, 'shortaddress':shortaddress, 'city':city, 'country':country, 'code':country_code, 'county':county, 'postcode':postcode, 'road':road, 'state':state, 'suburb':suburb}




