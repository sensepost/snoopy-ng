This is a temporary readme file, a more formal one will be built
for the release.


-------

Extract the archive:

tar czf snoopy_ng.tar.gz
cd snoopy_ng

Run the dependencies installer:

bash install.sh

Then to run Snoopy:

snoopy -h [get help]
snoopy -i [list all plugins]

As an example, to use the WiFi plugin, which has several subplugins
as you'll notice from the above output:

snoopy -m c80211:iface=mon0 --drone myDrone --location someLocation
--verbose #Requires mon0 to be in monitor mode

( or c80211:mon=True, which will enable monitor mode for you on the
first available device )

If you want to sync data to a server:

#On server:
python snoopy_ng/includes/auth_handler.py --create myDrone
snoopy -m server

#On client, collect + sync
snoopy -m c80211:iface=mon0 --drone myDrone --location someLocation
--verbose --server http://<server_ip>:<port>

#Or just sync data:
snoopy --server http://<server_ip>:<port> --verbose

You'll get instructions for each plugin when you do the 'snoopy -i'.
They're of the form:

snoopy -m <plugin_name>[:option1=val1,option2=val2]

You can specify multiple plugins at once. So, if we want to run the
wireless (c80211) on our client, and then run the server plugin and
wigle plugin on our server:


#Client:
snoopy -m c80211:iface=mon0 --drone myDrone --location someLocation
--verbose --server http://<server_ip>:<port>

#Server:
snoopy -m server -m
wigle:username=<wigleuser>,password=<wiglepassword>,email=<me@moo.com>

By default snoopy will save to snoopy.db (sqlite) in it's directory. You
can specify your database type/location with the --dbms flag. I've
tested it with sqlite and mysql, but it should support anything that
sqlalchemy does, of the form:

dialect+driver://username:password@host:port/database

e.g:
snoopy -m server --dbms mysql://someuser:somepass@localhost/snoopy

For Maltego, when you run the install.sh script it should create a
symlink from snoopy_ng/transforms to /etc/transforms. You should just
then be able from able to import the snoopy tgz file from the transforms
directory. It should include local transforms + entities. Oh, you'll
need to set your db schema in this file:

snoopy_ng/transforms/db_path.conf
