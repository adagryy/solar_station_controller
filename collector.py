#!/usr/bin/env python
import psutil
import redis
from time import sleep

r = redis.Redis(host='localhost', port=6379, db=0)

while True:
    sleep(0.5)
    # print('CPU usage: ' + str(psutil.cpu_percent()))
    r.set('cpu', psutil.cpu_percent())
    print('CPU from db: ' + str(float(r.get('cpu'))))
# gives an object with many fields
# print(psutil.virtual_memory())
# you can convert that object to a dictionary 
# print(dict(psutil.virtual_memory()._asdict())['total'])
