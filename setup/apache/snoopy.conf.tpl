<VirtualHost *:9001>
    SetEnv SNOOPY_DBMS [SQL_ALCHEMY_DBMS]
    # Remove the below line if unsure
    ServerName [IP_OR_FQDN]

    SSLEngine On
    SSLCertificateFile /etc/apache2/ssl/apache.crt
    SSLCertificateKeyFile /etc/apache2/ssl/apache.key
    # The below line is not required for self-signed certs
    # SSLCertificateChainFile [PATH_TO_SSL_CERT_CHAIN.crt]

    WSGIDaemonProcess snoopy user=www-data group=www-data threads=5
    WSGIScriptAlias / /var/www/snoopy/snoopy.wsgi
    WSGIPassAuthorization On

    <Directory /var/www/snoopy>
        WSGIProcessGroup snoopy
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>
</VirtualHost>
