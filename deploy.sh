#!/bin/bash

# Pull newest version of application from git repository
git pull

# Stop collector service and Django app
sudo systemctl stop daphne.service
sudo systemctl stop collector.service

# Remove old collector and Django app source code
sudo rm -Rf /opt/mirrorcontroller/mirrors/
sudo rm -f /opt/mirrorcontroller/collector.py

# Copy new sources to their destinations
sudo cp /home/pi/solar_station_controller/collector.py /opt/mirrorcontroller/
sudo cp -R /home/pi/solar_station_controller/mirrors/ /opt/mirrorcontroller/

# Copy static files to their destinations
sudo rm -Rf /var/www/collector/*
sudo cp -R /home/pi/solar_station_controller/mirrors/webapp/static/* /var/www/collector/

# Start collector and Django application
sudo systemctl start collector.service
sudo systemctl start daphne.service
