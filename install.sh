#!/bin/bash

apt update
apt upgrade -y
apt install -y acl python3-pip apache2 php libapache2-mod-php

su ray -c 'pwd'
echo "alias python=python3" >> ~ray/.bashrc
echo "alias pip=pip3" >> ~ray/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~ray/.bashrc
su ray -c 'ssh-keygen -f ~/.ssh/id_rsa -N ""'
cat ~ray/.ssh/id_rsa.pub >> ~ray/.ssh/authorized_keys
su ray -c 'pip install -U ray pandas tabulate'

chown www-data:www-data ~www-data
su www-data -s /bin/bash -c 'ssh-keygen -f ~/.ssh/id_rsa -N ""'
cat ~www-data/.ssh/id_rsa.pub >> ~ray/.ssh/authorized_keys

mkdir /opt/electricitysim
cd /opt/electricitysim/
git clone git@github.com:tjones60/electricitysim.git .
setfacl -m u:ray:rwx ray/output.json
setfacl -m u:ray:rwx ray/plot.json
mkdir www/jobs
setfacl -Rm u:www-data:rwx www/jobs
setfacl -Rdm u:www-data:rwx www/jobs

echo "<VirtualHost *:80>
    DocumentRoot /opt/electricitysim/www

    <Directory /opt/electricitysim/www/>
        Options Indexes FollowSymLinks
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>" > /etc/apache2/sites-available/000-electricitysim.conf

a2dissite 000-default
a2ensite 000-electricitysim
systemctl restart apache2
