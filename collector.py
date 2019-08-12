#!/usr/bin/env python
import psutil
import redis
from time import sleep
import random

r = redis.Redis(host='localhost', port=6379, db=0)

# Enables pump for specific amount of time
def enable_pump(time):
    # enable_pump_gpio
    sleep(time)
    # disable_pump_gpio

# Decides if pump should be enabled
def should_pump_be_enabled(left, middle, right, launching):
    return False #left > launching or middle > launching or right > launching

while True:
    # Reading delay
    sleep(int(r.get('interval')))
    
    # Get temperatures from sensors
    left_sensor_temperature = random.uniform(20, 80)
    middle_sensor_temperature = random.uniform(20, 80)
    right_sensor_temperature = random.uniform(20, 80)
    tank_sensor_temperature = random.uniform(20, 80)

    # Get the pump launching temperature; if absorber exceeds this temperature, pump then is launched
    pump_launching_temperature = int(r.get('pumpLaunchingTemperature'))
    
    # Run pump if necessarry
    if should_pump_be_enabled(left_sensor_temperature, middle_sensor_temperature, right_sensor_temperature, pump_launching_temperature):
        enable_pump(int(redisDbReference.get('pumpTime')))
    r.set('left_sensor_temperature', left_sensor_temperature)
    r.set('middle_sensor_temperature', middle_sensor_temperature)
    r.set('right_sensor_temperature', right_sensor_temperature)    
    r.set('tank_sensor_temperature', tank_sensor_temperature)
    # print('CPU from db: ' + str(float(r.get('cpu'))))
# gives an object with many fields
# print(psutil.virtual_memory())
# you can convert that object to a dictionary 
# print(dict(psutil.virtual_memory()._asdict())['total'])
