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

if __name__ == "__main__":
    import sys, argparse, requests, re
    from urlparse import urlparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--update", help="Update OUI data from known remote IEEE text file", action='store_true')
    parser.add_argument("-f", "--file", help="The location of oui.txt file")
    args = parser.parse_args()

    if not args.update:
        print "[!] No operation specified! Try --help."
        sys.exit(-1)

    if not args.file:
        args.file = "https://code.wireshark.org/review/gitweb?p=wireshark.git;a=blob_plain;f=manuf;hb=HEAD"

    o = urlparse(args.file)

    print "[+] Fetching data from %s..."%args.file

    if not o.scheme or o.scheme == "file":
        with open(args.file, "r") as f:
            data = f.read()
    elif o.scheme == "http" or o.scheme == "https":
        r = requests.get(args.file)
        data = r.text.encode("utf8")
    else:
        print "[!] Only local files or http(s) URLs are supported."
        sys.exit(-1)

    count = 0
    f = open("%s/mac_vendor.txt"%path, "w")
    for line in data.split('\n'):
        try:
            mac, vendor = re.search(r'([0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2})\t(.*)', line).groups()
            vendor = vendor.split("# ")
            vendorshort = vendor[0].strip()
            vendorlong = vendorshort
            if (len(vendor) == 2):
                vendorlong = vendor[1].strip()
            f.write("|".join((mac.replace(":", "").upper(), vendorshort, vendorlong + "\n")))
            count += 1
        except AttributeError:
            continue
        except:
            print "[!] Processing error - you may need to restore mac_vendor.txt manually."
            sys.exit(-1)

    f.close()
    print "[+] Wrote %d OUI entries"%count



