#!/bin/bash

# before running this script, review all commands and comment out any
# that aren't applicable to your setup or have already been run.
# the ray user should already exist on this system and any other system
# that will be used as a worker. ssh keys should be copied between the
# ray users on all computers (or use ldap account with shared home dir).
# python, pip, ray, pandas, and tabulate need to be install on all workers.
# this script otherwise generally assumes a fresh ubuntu install with
# no other services running

# install packages with apt
apt update
apt upgrade -y
apt install -y acl python3 python3-pip apache2 php libapache2-mod-php

# initialize ray user home directory
su ray -c 'echo ~'

# append to bashrc
echo "alias python=python3" >> ~ray/.bashrc
echo "alias pip=pip3" >> ~ray/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~ray/.bashrc

# ray ssh-keygen and copy id to self
su ray -c 'ssh-keygen -f ~/.ssh/id_rsa -N ""'
su ray -c 'touch ~/.ssh/authorized_keys'
cat ~ray/.ssh/id_rsa.pub >> ~ray/.ssh/authorized_keys

# install required pip packages
su ray -c 'pip3 install -U ray pandas tabulate'

# www-data ssh-keygen and copy if to ray
chown www-data:www-data ~www-data
su www-data -s /bin/bash -c 'ssh-keygen -f ~/.ssh/id_rsa -N ""'
cat ~www-data/.ssh/id_rsa.pub >> ~ray/.ssh/authorized_keys

# initialize electricity sim dir
mkdir /opt/electricitysim
cd /opt/electricitysim/
git clone https://github.com/tjones60/electricitysim.git .
setfacl -m u:ray:rwx ray/output.json
setfacl -m u:ray:rwx ray/plot.json
mkdir www/jobs
setfacl -Rm u:www-data:rwx www/jobs
setfacl -Rdm u:www-data:rwx www/jobs
setfacl -Rm u:ray:rwx www/jobs
setfacl -Rdm u:ray:rwx www/jobs

# create apache vhost
echo "<VirtualHost *:80>
    DocumentRoot /opt/electricitysim/www

    <Directory /opt/electricitysim/www/>
        Options Indexes FollowSymLinks
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>" > /etc/apache2/sites-available/000-electricitysim.conf

# disable default site and enable new site
a2dissite 000-default
a2ensite 000-electricitysim
systemctl restart apache2
