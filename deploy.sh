#!/bin/bash
git pull
sudo systemctl stop daphne.service
sudo systemctl stop collector.service
sudo rm -Rf /opt/mirrorcontroller/mirrors/
sudo rm -f /opt/mirrorcontroller/collector.py
sudo cp /home/pi/solar_station_controller/collector.py /opt/mirrorcontroller/
sudo cp -R /home/pi/solar_station_controller/mirrors/ /opt/mirrorcontroller/
sudo systemctl start collector.service
sudo systemctl start daphne.service
