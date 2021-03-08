#!/bin/bash

echo "alias python=python3" >> ~/.bashrc
echo "alias pip=pip3" >> ~/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

sudo apt update
sudo apt upgrade
sudo apt install python3-pip

pip install -U ray
pip install -U pandas
pip install -U tabulate

sudo mkdir /opt/electricitysim
cd /opt/electricitysim/
sudo chown tjones60:calpoly .
setfacl -Rm g::rwx .
setfacl -Rdm g::rwx .
git clone git@github.com:tjones60/electricitysim.git .
cd ray
ray up -y cluster.yaml
ray attach cluster.yaml
python simulate.py config.ini output.json
ssh ray@192.168.2.231 '~/.local/bin/ray exec /opt/electricitysim/ray/cluster.yaml "python3 /opt/electricitysim/ray/simulate.py /opt/electricitysim/www/jobs/config.json /opt/electricitysim/www/jobs/output.json"'