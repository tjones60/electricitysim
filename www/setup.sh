#!/bin/bash

apt update
apt upgrade -y
apt install -y python3-pip

mkdir /opt/electricitysim
cd /opt/electricitysim/
git clone git@github.com:tjones60/electricitysim.git .
sudo chown -R tjones60:calpoly .
setfacl -Rm g::rwx .
setfacl -Rdm g::rwx .
#ssh ray@192.168.2.21 '~/.local/bin/ray up /opt/electricitysim/ray/cluster.yaml'