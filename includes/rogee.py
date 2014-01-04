from run_prog import run_program
import time
import netifaces
import logging
import sys

# Var to hold external processes:
procs = {}

# Vars for access point
ssid = "tubes"
mon_iface = "mon0"
airb_opts = ['-e', ssid, '-P', mon_iface]
airb_cmd = ['airbase-ng'] + airb_opts
airb_cmd = " ".join(airb_cmd) 

# Var for setting access point IP
set_ip_cmd = "ifconfig at0 up 10.0.0.1 netmask 255.255.255.0"

# Vars for DHCP server
config_file = """
dhcp-range=10.0.0.2,10.0.0.100,255.255.255.0,8765h
dhcp-option=3,10.0.0.1
dhcp-option=6,8.8.8.8
dhcp-leasefile=/etc/dhcpd.leases
"""
f=open('/etc/dnsmasq.conf', 'w')
f.write(config_file)
f.close()
launch_dhcp = "dnsmasq -d -a 10.0.0.1 -i at0 -C /etc/dnsmasq.conf"

#Start airbase
run_program("killall airbase-ng")
time.sleep(4)

# Make sure interface exists
if mon_iface not in netifaces.interfaces():
	logging.error("No such interface: '%s'" % mon_iface)
	sys.exit(-1)
proc = run_program(airb_cmd)
if proc.poll():
	logging.error("Airbase has terminated. Cannot continue.")
	sys.exit(-1)

# Wait for airbase at0 interface to come up
while "at0" not in netifaces.interfaces():
	logging.debug("Waiting for airbase interface to come up.")
	time.sleep(1)

procs['airbase'] = proc
logging.debug("Airbase interface is up. Setting IP...")
run_program(set_ip_cmd)

# Wait for IP to be set
ipSet = False
while not ipSet:
	try:
		if netifaces.ifaddresses('at0')[2][0]['addr']:
			ipSet = True
	except Exception:
		time.sleep(2)
		pass

logging.info("IP address for access point has been set. Starting DHCP server...")

# Start DHCP server
run_program("killall dnsmasq")
time.sleep(3)
proc = run_program(launch_dhcp)
if proc.poll():
	response = proc.communicate()
	response_stdout, response_stderr = response[0], response[1]
	if response_stderr:
		logging.error(response_stderr)
	else:
		logging.error("Unable to launch dhcp server.")
	#sys.exit(-1)

procs['dhcp'] = proc


# Handle NAT
ipt = ['iptables -F', 'iptables -F -t nat', 'iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE',  'iptables -A FORWARD -i at0 -o eth0 -j ACCEPT']
for rule in ipt:
	run_program(rule)

run_program("echo '1' > /proc/sys/net/ipv4/ip_forward")


# Ensure DHCP + AP remain up.
for name, proc in procs.iteritems():
	if proc.poll():
		logging.error("Process for %s has died, cannot continue. Sorry." % name) 


