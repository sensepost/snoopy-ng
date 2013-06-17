1. Install base Ubuntu Image on an SD card:
wget http://s3.armhf.com/debian/precise/bone/ubuntu-precise-12.04.2-armhf-3.8.13-bone20.img.xz
xz -cd ubuntu-precise-12.04.2-armhf-3.8.13-bone20.img.xz > /dev/sd_YOUR_SD_CARD

2. Insert SD card to device, SSH in (ubuntu:ubuntu), and place files in this folder:
/home/ubuntu/snoopy_ng/

If you wish to put them elsewhere, make sure you edit ./setup/upstarts/*.conf to relfect
the new location of ./setup/upstarts/SETTINGS

3. Go through INSTALL.sh. I'd recommend manually running these commands to watch out for errors. 

4. Copy the autostart scripts:
cp /home/ubuntu/snoopy_ng/setup/upstarts/*.conf /etc/init/


5. Start the drone_conf service:
service_start drone_config

6. Setup your Sensor number here:
http://<your_device_ip>:5000/set_sensor_id?id=XX

The default value is 99 (and this you will see 'sensor99' data in the database).



On the server side place, do the following:

1. Make apprpriate changes in ./includes/webserverOptions.py to relfect your database
requirements (default will be to save to sqlite (snoopy.db)).

2. Install these packages and the SSL key:
apt-get install apache2
apt-get install libapache2-mod-wsgi
a2enmod ssl
service apache2 restart
mkdir /etc/apache2/ssl
openssl req -x509 -nodes -days 1000 -newkey rsa:2048 -keyout /etc/apache2/ssl/apache.key -out /etc/apache2/ssl/apache.crt

cp ./setup/apache/snoopy /etc/apache2/sites-available/
ln -s /etc/apache2/sites-available/snoopy /etc/apache2/sites-enabled/snoopy

a2ensite snoopy
service apache restart

3. Drones require accounts to be created to sync:
snoopy.py -n somedrone

Ensure the key generated is reflected in your client SETTINGS file.
