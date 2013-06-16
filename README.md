Writing the image

wget http://s3.armhf.com/debian/precise/bone/ubuntu-precise-12.04.2-armhf-3.8.13-bone20.img.xz
xz -cd ubuntu-precise-12.04.2-armhf-3.8.13-bone20.img.xz > /dev/sd_YOUR_SD_CARD


Server Setup

#SSL
apt-get install apache2
apt-get install libapache2-mod-wsgi
a2enmod ssl
service apache2 restart
mkdir /etc/apache2/ssl
openssl req -x509 -nodes -days 1000 -newkey rsa:2048 -keyout /etc/apache2/ssl/apache.key -out /etc/apache2/ssl/apache.crt
a2ensite snoopy
service apache restart
