#!/usr/bin/env python
import psutil
import redis
from time import sleep
import random
import threading

# Establish connection with Redis store
r = redis.Redis(host='localhost', port=6379, db=0)
global pumpEnabled
pumpEnabled = False

# Enables pump for specific amount of time in new thread
def enable_pump():	
    while True:
        # Read, how much time pump should be enabled at once
        time = int(r.get('pumpTime'))
        sleep(0.5)

        # Flag saying pump should be enabled
        if pumpEnabled or str_to_bool(r.get('other')): # This condition is as follows: if pump should be enabled according to automatic mode or manual mode
            r.set('pump_state', 1) # Save to database, that pump is enabled
            print("Pump state: ON")            	
        	# if gpio.LOW            
            #     enable gpio
            #     sleep(time)        
        if not pumpEnabled and not str_to_bool(r.get('other')): # This condition is as follows: if pump should be disabled according to automatic mode and manual mode
            r.set('pump_state', 0) # Save to database, that pump is disabled
            print("Pump state: OFF") 
            # if gpio.HIGH 
            #     disable gpio

# Decides if pump should be enabled
def should_pump_be_enabled(left, middle, right, launching):
    return (left > launching or middle > launching or right > launching) and str_to_bool(r.get('automatic')) # Check, if pump should be launched depending on temperature measurement and only in automatic mode pump can be enabled automatically

# This helper is used to convert booleans from database read as a string to Pythons' bool type
def str_to_bool(s):
    s = s.decode('utf-8')
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError 

thread = threading.Thread(target=enable_pump, args=())
thread.start()

while True:
    # Reading delay
    sleep(int(r.get('interval')))    
    
    # Get temperatures from sensors
    left_sensor_temperature = round(random.uniform(20, 80))
    middle_sensor_temperature = round(random.uniform(20, 80))
    right_sensor_temperature = round(random.uniform(20, 80))
    tank_sensor_temperature = round(random.uniform(20, 80))   

    # Get the pump launching temperature; if absorber exceeds this temperature, pump then is launched
    pump_launching_temperature = int(r.get('pumpLaunchingTemperature'))

    print("Interval: " + str(int(r.get('interval'))) + ", launch: " + str(pump_launching_temperature) + ", left: " + str(left_sensor_temperature) + ", middle: " + str(middle_sensor_temperature) + ", right: " + str(right_sensor_temperature) + ", tank: " + str(tank_sensor_temperature))
    
    # Set flag indicating enabling/disabling the pump
    pumpEnabled = should_pump_be_enabled(left_sensor_temperature, middle_sensor_temperature, right_sensor_temperature, pump_launching_temperature)     

    r.set('left_sensor_temperature', left_sensor_temperature)
    r.set('middle_sensor_temperature', middle_sensor_temperature)
    r.set('right_sensor_temperature', right_sensor_temperature)    
    r.set('tank_sensor_temperature', tank_sensor_temperature)