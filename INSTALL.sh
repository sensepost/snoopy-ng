#!/bin/bash
set -e

echo "[+] Setting time with ntp"
ntpdate ntp.ubuntu.com 
echo "[+] Setting timzeone..."
echo "Europe/London" > /etc/timezone
dpkg-reconfigure -f noninteractive tzdata
echo "[+] Installing sakis3g..."
cp ./includes/sakis3g /usr/local/bin

echo "[+] Updating repository..."
apt-get update

# Packages
echo "[+] Installing required packages..."
apt-get install --force-yes --yes autossh python-psutil python2.7-dev libpcap0.8-dev python-sqlalchemy ppp tcpdump python-serial sqlite3 python-requests iw build-essential python-bluez python-flask

# Download & Installs
echo "[+] Downloading pylibpcap..."
wget http://switch.dl.sourceforge.net/project/pylibpcap/pylibpcap/0.6.4/pylibpcap-0.6.4.tar.gz
tar xzf pylibpcap-0.6.4.tar.gz
cd pylibpcap-0.6.4
echo "[-] Installing pylibpcap..."
python setup.py install

cd ..
rm -rf pylibpcap-0.6.4*
echo "[+] Downloading dpkt..."
wget http://dpkt.googlecode.com/files/dpkt-1.8.tar.gz
tar xzf dpkt-1.8.tar.gz 
cd dpkt-1.8
echo "[-] Installing dpkt..."
python setup.py install
cd ..
rm -rf dpkt-1.8*

cd setup 
echo "[+] Installing patched version of scapy..."
tar xzf scapy-latest-snoopy_patch.tar.gz
cd scapy-2.1.0 
python setup.py install
cd ..
rm -rf scapy-2.1.0
cd ..

# Only run this on your client, not server:
echo "[+] Downloading aircrack-ng..."
wget http://download.aircrack-ng.org/aircrack-ng-1.2-beta1.tar.gz
tar xzf aircrack-ng-1.2-beta1.tar.gz
cd aircrack-ng-1.2-beta1
make
echo "[-] Installing aircrack-ng"
make install
cd ..
rm -rf aircrack-ng-1.2-beta1*
