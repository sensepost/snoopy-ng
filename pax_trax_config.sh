#!/bin/bash

echo "This script will prepare the Sensor for PAX TRAX"
echo "Please make sure you're running this from /home/ubuntu/snoopy_ng"

echo "Installing packages and required software"
read -p "Press any key to continue"
bash INSTALL.txt

echo "Setting eth0 to static IP address of 192.168.100.13 (only to reflect on reboot)"

cat > /etc/network/interface << EOL
cat > interface << EOL
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
address 192.168.100.13
netmask 255.255.255.0

EOL

echo "Copying upstarts"
cp /home/ubuntu/snoopy_ng/setup/upstarts/*.conf /etc/init/
echo "Starting Sensor ID config page"
service_start drone_config

echo "Please go to "http://<this_device_ip>:5000/set_sensor_id?id=<set_number_here>
echo "After doing so, reboot, and data should appear in the remote database"
