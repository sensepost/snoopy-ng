These instructions were tested against Ubuntu 12/14 LTS.

All commands need to be ran as root or via sudo.

1. Install Apache
=================

Run the following commands in the terminal:

```bash
apt-get install -y apache2 libapache2-mod-wsgi
a2enmod ssl
a2enmod env
service apache2 restart
```

Enable the required custom port (9001 or another):

```bash
nano /etc/apache2/ports.conf
```

Add the following line right under "Listen 80":

```
Listen 9001
```

2. Obtain SSL Certificate
=========================

Obtain a commercial SSL cert or generate a self-signed one. Beware, the latter leaves the data syncing by drones more prone to MitM attacks.

A self-signed cert can be generated using:

```bash
mkdir /etc/apache2/ssl
openssl req -x509 -nodes -days 1000 -newkey rsa:2048 -keyout /etc/apache2/ssl/apache.key -out /etc/apache2/ssl/apache.crt
```

3. Enable snoopy-ng Server
==========================

Create a symlink to the WSGI script:

```bash
mkdir /var/www/snoopy
cd [SNOOPY_CHECKOUT_DIR]
ln -s $PWD/setup/apache/snoopy.wsgi /var/www/snoopy/snoopy.wsgi
mkdir /var/www/.pyrit
chown www-data:www-data /var/www/.pyrit/
```

Create a configuration file from template:

```bash
cd [SNOOPY_CHECKOUT_DIR]
cp ./setup/apache/snoopy.conf.tpl /etc/apache2/sites-available/snoopy.conf
ln -s /etc/apache2/sites-available/snoopy.conf /etc/apache2/sites-enabled/snoopy.conf
```

Open /etc/apache2/sites-enabled/snoopy.conf in your editor of choice and updated the variable placeholders to reflect your specific circumstances. Specifically, look at the following:

* [SQL_ALCHEMY_DBMS] - the DB connection string (refer to main README)
* [IP_OR_FQDN] - the IP address or FQDN of the server
* [PATH_TO_SSL_CERT_CHAIN.crt] - path to the cert chain file (optional)
* /etc/apache2/ssl/apache.crt - path to the certificate file (optional)
* /etc/apache2/ssl/apache.key - path to the certificate key file (optional)

Once updated, apply the config:

```bash
a2ensite snoopy
service apache2 restart
```

Don't forget to check for any blocking firewall rules if you can't get to the syncing agent.
