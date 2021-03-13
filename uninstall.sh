#!/bin/bash

a2dissite 000-electricitysim
a2ensite 000-default
systemctl restart apache2
rm /etc/apache2/sites-available/000-electricitysim.conf
rm -r /opt/electricitysim
rm -r ~ray/*
rm -r ~www-data/.ssh
