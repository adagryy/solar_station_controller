#!/usr/bin/env python
import psutil
import redis
from time import sleep
import random

r = redis.Redis(host='localhost', port=6379, db=0)

while True:
    sleep(0.99)
    # print('CPU usage: ' + str(psutil.cpu_percent()))
    r.set('right_sensor_temperature', random.uniform(20, 80))
    r.set('middle_sensor_temperature', random.uniform(20, 80))
    r.set('left_sensor_temperature', random.uniform(20, 80))
    r.set('tank_sensor_temperature', random.uniform(20, 80))
    # print('CPU from db: ' + str(float(r.get('cpu'))))
# gives an object with many fields
# print(psutil.virtual_memory())
# you can convert that object to a dictionary 
# print(dict(psutil.virtual_memory()._asdict())['total'])
