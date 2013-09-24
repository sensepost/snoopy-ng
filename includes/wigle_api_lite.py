#!/usr/bin/python
# coding=utf-8
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# Crude wigle web API. The non-lite version supports multiple proxies 
# each with their own wigle account, but this violates Wigle policies
# (and is therefore not going to be given to you).
# Go join Wigle and support their project, they're an aweomse bunch.

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
#import urllib2
#import httplib2
#import urllib
import json

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

pp = pprint.PrettyPrinter(indent=4)
fd=os.path.dirname(os.path.realpath(__file__))
tmp=re.search('(^.*)\/.*',fd)
save_dir="%s/web_data/street_views"%tmp.group(1)

def wigle(account,ssid):

    url={'land':"https://wigle.net/", 'login': "https://wigle.net/gps/gps/main/login", 'query':"http://wigle.net/gps/gps/main/confirmquery/"}

    #1. Create HTTP objects with proxy
    user,password,proxy=account
    proxies = {"http":proxy,"https":proxy}  
    #2. Log in to Wigle
    #logging.debug("[+] Logging into wigle with %s:%s via proxy '%s'" %(user,password,proxy))
    payload={'credential_0':user, 'credential_1':password}
    try:
        r = requests.post(url['login'],data=payload,proxies=proxies,timeout=10)
    except Exception, e: #(requests.exceptions.ConnectionError,requests.exceptions.Timeout), e:
        logging.debug("[E] Unable to connect via proxy %s. Thread returning." %(proxy))
        return {'error':e}
    if( 'Please login' in r.text or 'auth' not in r.cookies):
        logging.debug("[-] Error logging in with credentials %s:%s. Thread returning." %(user,password))
        return {'error':'Unable to login to wigle'}
        #exit(-1)
    #else:
    #    logging.debug("[-] Successfully logged in with credentials %s:%s via %s." %(user,password,proxy))
    cookies=dict(auth=r.cookies['auth'])
    #3. Poll SSID queue
    #logging.debug("[-] Looking up %s (%s %s)" %(ssid,user,proxy))
    payload={'longrange1': '', 'longrange2': '', 'latrange1': '', 'latrange2':'', 'statecode': '', 'Query': '', 'addresscode': '', 'ssid': ssid.replace("_","\_"), 'lastupdt': '', 'netid': '', 'zipcode':'','variance': ''}
    try:
        r = requests.post(url['query'],data=payload,proxies=proxies,cookies=cookies,timeout=10)
        if( r.status_code == 200):
            if('too many queries' in r.text):
                logging.debug("[-] User %s has been shunned, pushing %s back on queue... Sleeping for 10 minutes..." %(user,ssid))
            elif('An Error has occurred:' in r.text):
                logging.debug("[-] An error occured whilst looking up '%s' with Wigle account '%s' (via %s)!" % (ssid,user,proxy))
                return {'error':'Text response contained "An Error has occurred"'}
            elif('Showing stations' in r.text):
                locations=fetch_locations(r.text,ssid)
                #pp.pprint(locations)
                return locations
            else:
                logging.debug("[-] Unknown error occured whilst looking up '%s' with Wigle account '%s' (via %s)!" % (ssid,user,proxy))
                #exit(-1)
        else:
            logging.debug("[-] Bad status - %s" %r.status_code)
            return {'error':'Bad HTTP status - %s'%r.status_code}
    
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout), e:
        logging.debug("[-] Exception. Unable to retrieve SSID '%s' with creds %s:%s via '%s'." %(ssid,user,password,proxy))
        return {'error':e}
    


def fetch_locations(text,ssid):
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
            dist=haversine(float(locations[i]['lat']),float(locations[i]['long']),float(locations[j]['lat']),float(locations[j]['long']))
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

def haversine(lat1, lon1, lat2, lon2):
    R = 6372.8 # In kilometers
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.sin(dLon / 2) * math.sin(dLon / 2) * math.cos(lat1) * math.cos(lat2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c * 1000.0 # In metres


def getAddress(gps_lat,gps_long):
    lookup_url = "http://nominatim.openstreetmap.org/reverse?zoom=18&addressdetails=1&format=json&email=glenn@sensepost.com&lat=%s&lon=%s" %(gps_lat,gps_long)
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

def fetchLocations(ssid):
    global save_dir

    if not os.path.exists(save_dir) and not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    #logging.debug("Wigling %s"%ssid)
    try:
        f=open("%s/wigle_creds.txt"%fd)
        line=f.readline().strip()
        user,passw,proxy=line.split(':')
    except Exception,e:
        logging.error("Unable to load Wigle creds from 'wigle_creds.txt'!")
        return {'error':'Unable to load creds from wigle_creds.txt'}
    account=(user,passw,proxy)
    #logging.info("Using Wigle account %s"%user)

    if user=='setYourWigleUsername':
        return {'error':'Wigle credentials not set'}

    locations=wigle(account,ssid)

    if locations != None and 'error' not in locations:
        if (locations != None and locations[0]['overflow'] == 0):   
            for l in locations:
                l.update(getAddress(l['lat'],l['long']))
    return locations

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    if ( len(sys.argv) < 2):
        logging.error("Usage: wigle_api_lite.py <ssid>")
        sys.exit(-1)

    ssid=sys.argv[1]
    pp.pprint(fetchLocations(ssid))

