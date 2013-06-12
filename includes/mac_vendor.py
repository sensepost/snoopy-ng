import os

#Set path
path=os.path.dirname(os.path.realpath(__file__))

class mac_vendor():
    def __init__(self):
        self.mac_lookup = {}
        with open("%s/mac_vendor.csv"%path) as f:
            for line in f:
                (key, val) = line.split(",")
                self.mac_lookup[key.lower()] = val.strip()

    def lookup(self,mac):
        mac = mac.lower()
        if mac in self.mac_lookup:
            return self.mac_lookup[mac]
        else:
            return ""
