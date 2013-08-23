import os

#Set path
path=os.path.dirname(os.path.realpath(__file__))

class mac_vendor():
    def __init__(self):
        self.mac_lookup = {}
        with open("%s/mac_vendor.txt"%path) as f:
            for line in f:
                line = line.strip()
                (mac, vendorshort, vendorlong) = line.split("|")
                self.mac_lookup[mac.lower()] = (vendorshort, vendorlong)

    def lookup(self,mac):
        mac = mac.lower()
        if mac in self.mac_lookup:
            return self.mac_lookup[mac]
        else:
            return ("Unknown", "Unknown device")
