#!/bin/bash

sudo mkdir /opt/electricitysim
cd /opt/electricitysim/
sudo chown tjones60:calpoly .
setfacl -Rm g::rwx .
setfacl -Rdm g::rwx .
git clone git@github.com:tjones60/electricitysim.git .
cd ray
ray up -y cluster.yaml
ray attach cluster.yaml
RAY_ADDRESS=auto python simulate.py config.ini output.json