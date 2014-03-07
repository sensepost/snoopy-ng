from run_prog import run_program
import time
import netifaces
import logging
import sys
import includes.monitor_mode as mm
from collections import deque
import pyinotify
import os
from includes.fonts import *

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_MODIFY(self, event):
        self.someInstance.check_new_leases()

class rogueAP:
    """Create a rogue access point"""
    def __init__(self, **kwargs):

        self.ssid = kwargs.get("ssid", "FreeInternet")
        self.wlan_iface = kwargs.get("wlan_iface", None)    # If none, will use first wlan capable of injection
        self.net_iface = kwargs.get("net_iface", "eth0")    # iface with outbound internet access
        self.enable_mon = kwargs.get("enable_mon", False)   # airmon-ng start <wlan_iface> 
        self.promisc =   kwargs.get("promisc", False)       # Answer all probe requests

        self.procs = {} #Var to hold external processes, and ensure they keep running
        self.num_procs = 2 # How many procs should be run
        self.verb = kwargs.get('verbose', 0)

        self.already_seen={}
        self.new_leases = deque()

        if self.promisc == "True":
            self.promisc = True
        else:
            self.promisc = False
        if self.enable_mon == "True":
            self.enable_mon = True
        else:
            self.enable_mon = False

        if self.enable_mon:
            self.wlan_iface=mm.enable_monitor_mode(self.wlan_iface)

        if not self.wlan_iface:
            logging.error("No wlan_iface specified for rogueAP :(")
            sys.exit(-1)        
        if self.promisc:    
            airb_opts = ['-e', self.ssid, '-P', self.wlan_iface]
        else:
            airb_opts = ['-e', self.ssid, self.wlan_iface]
        self.airb_cmd = ['airbase-ng'] + airb_opts
        self.airb_cmd = " ".join(self.airb_cmd)      
        self.set_ip_cmd = "ifconfig at0 up 10.0.0.1 netmask 255.255.255.0"  

        
        # Vars for DHCP server
        config_file ="""
dhcp-range=10.0.0.2,10.0.0.100,255.255.255.0,8765h
dhcp-option=3,10.0.0.1
dhcp-option=6,8.8.8.8
dhcp-leasefile=/etc/dhcpd.leases
"""
        f=open('/etc/dnsmasq.conf', 'w')
        f.write(config_file)
        f.close()
        self.launch_dhcp = "dnsmasq -d -a 10.0.0.1 -i at0 -C /etc/dnsmasq.conf"

        # Monitor dhcpd.lease file for updates
        with file("/etc/dhcpd.leases", 'a'):
            os.utime("/etc/dhcpd.leases", None)

        wm = pyinotify.WatchManager() # Watch Manager
        wdd = wm.add_watch('/etc/dhcpd.leases', pyinotify.IN_MODIFY, rec=True)

        handler = EventHandler()
        handler.someInstance = self

        self.notifier = pyinotify.ThreadedNotifier(wm, handler)
        self.notifier.start()


    def run_ap(self):
        run_program("killall airbase-ng")
        time.sleep(4)

        # Make sure interface exists
        if self.wlan_iface not in netifaces.interfaces():
            logging.error("No such interface: '%s'" % self.wlan_iface)
            return False
        proc = run_program(self.airb_cmd)
        if proc.poll():
            logging.error("Airbase has terminated. Cannot continue.")
            return False

        # Wait for airbase at0 interface to come up
        while "at0" not in netifaces.interfaces(): #Should add a timeout
            logging.debug("Waiting for airbase interface to come up.")
            time.sleep(1)

        self.procs['airbase'] = proc
        logging.debug("Airbase interface is up. Setting IP...")
        run_program(self.set_ip_cmd)

        # Wait for IP to be set
        ipSet = False
        while not ipSet:
            try:
                if netifaces.ifaddresses('at0')[2][0]['addr']:
                    ipSet = True
            except Exception:
                time.sleep(2)
                pass

        logging.info("IP address for access point has been set.")
        return True
       
    def run_dhcpd(self):
        run_program("killall dnsmasq")
        time.sleep(3)
        proc = run_program(self.launch_dhcp)
        if proc.poll():
            response = proc.communicate()
            response_stdout, response_stderr = response[0], response[1]
            if response_stderr:
                logging.error(response_stderr)
            else:
                logging.error("Unable to launch dhcp server.")
                return False
        self.procs['dhcp'] = proc
        return True


    def check_new_leases(self):
        try:
            lines = [line.strip() for line in open('/etc/dhcpd.leases')]
        except Exception, e:
            logging.warning("Unable to open DHCP lease file. It's probably waiting to be created")
            return
        for line in lines:
            try:
                line = line.split()
                ltime, mac, ip = line[0], line[1], line[2]
                hostname = " ".join(line[3:-1])
                if mac not in self.already_seen:
                    self.new_leases.append({'mac':mac, 'leasetime':ltime, 'ip':ip, 'hostname':hostname})
                    self.already_seen[mac] = 1
                    if self.verb > 0:
                        logging.info("New %sDHCP lease%s handed out to %s%s (%s)%s" % (GR,G,GR,mac,hostname,G))
            except Exception,e:
                logging.error("Badly formed DHCP lease - '%s'" % line)

    def get_new_leases(self):
        #self.__check_new_leases()
        rtnData=[]
        while self.new_leases:
            rtnData.append(self.new_leases.popleft())
        if rtnData:
            return [("dhcp_leases", rtnData)]
        else:
            return []

    def do_nat(self):
        # Handle NAT
        ipt = ['iptables -F', 'iptables -F -t nat', 'iptables -t nat -A POSTROUTING -o %s -j MASQUERADE'%self.net_iface,  'iptables -A FORWARD -i at0 -o %s -j ACCEPT'%self.net_iface]
        for rule in ipt:
            run_program(rule)
        run_program("sysctl -w net.ipv4.ip_forward=1")

    def all_OK(self):
        # Ensure DHCP + AP remain up.
        if len(self.procs) < self.num_procs:
            return False # Still starting up
        for name, proc in self.procs.iteritems():
            if proc.poll():
                logging.error("Process for %s has died, cannot continue. Sorry." % name) 
                return False
        return True

    def shutdown(self):
        #Kill kill kill
        self.notifier.stop()
        run_program("killall airbase-ng")
        run_program("killall dnsmasq")
        run_program("iptables -F")
        run_program("killall -F -t nat")
        run_program("sysctl -w net.ipv4.ip_forward=0")
        os.remove("/etc/dhcpd.leases")
