#!/bin/bash

apt update
apt upgrade -y
apt install -y acl python3-pip apache2 php libapache2-mod-php

su ray
echo "alias python=python3" >> ~/.bashrc
echo "alias pip=pip3" >> ~/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
ssh-keygen -f ~/.ssh/id_rsa -N ''
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
exit

su ray
pip install -U ray
pip install -U pandas
pip install -U tabulate
exit

chown www-data:www-data ~www-data

su www-data -s /bin/bash
ssh-keygen -f ~/.ssh/id_rsa -N ''
exit

cat ~www-data/.ssh/id_rsa.pub >> ~ray/.ssh/authorized_keys

mkdir /opt/electricitysim
cd /opt/electricitysim/
git clone git@github.com:tjones60/electricitysim.git .
setfacl -m u:ray:rwx ray/output.json
setfacl -m u:ray:rwx ray/plot.json
mkdir www/jobs
setfacl -Rm u:www-data:rwx www/jobs
setfacl -Rdm u:www-data:rwx www/jobs


