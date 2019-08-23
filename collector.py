#!/usr/bin/env python
import psutil
import redis
import time
import random
import threading

# Establish connection with Redis store
r = redis.Redis(host='localhost', port=6379, db=0)
global pumpEnabled
pumpEnabled = False

# Setup initial data into Redis, if they are not defined there
def initialSetup():    
    automaticControl = r.get('automaticControl')
    manualControl = r.get('manualControl')    
    pumpLaunchingTemperature = r.get('pumpLaunchingTemperature')
    pumpWorkingTime = r.get('pumpWorkingTime')
    temperatureReadInterval = r.get('temperatureReadInterval')

    if not automaticControl:
        r.set('automaticControl', 'False')
    if not manualControl:
        r.set('manualControl', 'False')
    if not pumpLaunchingTemperature:
        r.set('pumpLaunchingTemperature', '60')
    if not pumpWorkingTime:
        r.set('pumpWorkingTime', '30')
    if not temperatureReadInterval:
        r.set('temperatureReadInterval', '2')

# Enables pump for specific amount of time in new thread
def enable_pump():
    currentRun = lastTimePumpEnabled = 0 #  lastTimePumpEnabled - remember, when pump was last time enabled - it can change state at least 10s from previous state change. 
    lastTimePumpDisabled = int(time.time())
    while True:
        # Read, how much time pump should be enabled at once
        delay = int(r.get('pumpWorkingTime'))
        time.sleep(0.5)

        currentRun = int(time.time()) # we measure time to compare when pump was last time enabled/disabled to avoid enabling/disabling pump too fast (i.e 3 time per second)

        # Flag saying pump should be enabled
        if (pumpEnabled or str_to_bool(r.get('manualControl'))) and (currentRun - lastTimePumpEnabled > 10) and (currentRun - lastTimePumpDisabled > 10): # This condition is as follows: if pump should be enabled according to automatic mode or manual mode
            lastTimePumpEnabled = int(time.time())
            r.set('pump_state', 1) # Save to database, that pump is enabled
            print("Pump state: ON")            	
        	# if gpio.LOW            
            #     enable gpio
            #     sleep(delay)        
        if (not pumpEnabled and not str_to_bool(r.get('manualControl'))) and (currentRun - lastTimePumpDisabled > 10) and (currentRun - lastTimePumpEnabled > 10): # This condition is as follows: if pump should be disabled according to automatic mode and manual mode
            lastTimePumpDisabled = int(time.time())
            r.set('pump_state', 0) # Save to database, that pump is disabled
            print("Pump state: OFF") 
            # if gpio.HIGH 
            #     disable gpio

# Decides if pump should be enabled
def should_pump_be_enabled(left, middle, right, launching):
    return (left > launching or middle > launching or right > launching) and str_to_bool(r.get('automaticControl')) # Check, if pump should be launched depending on temperature measurement and only in automatic mode pump can be enabled automatically

# This helper is used to convert booleans from database read as a string to Pythons' bool type
def str_to_bool(s):
    s = s.decode('utf-8')
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError 
# Start executing script
initialSetup()
thread = threading.Thread(target=enable_pump, args=())
thread.start()

while True:
    # Reading delay
    time.sleep(int(r.get('temperatureReadInterval')))    
    
    # Get temperatures from sensors (in production there should be real sensors connected)
    left_sensor_temperature = round(random.uniform(20, 80))
    middle_sensor_temperature = round(random.uniform(20, 80))
    right_sensor_temperature = round(random.uniform(20, 80))
    tank_sensor_temperature = round(random.uniform(20, 80))   

    # Get the pump launching temperature; if absorber exceeds this temperature, pump then is launched
    pump_launching_temperature = int(r.get('pumpLaunchingTemperature'))

    # print("temperatureReadInterval: " + strl(int(r.get('temperatureReadInterval'))) + ", launch: " + str(pump_launching_temperature) + ", left: " + str(left_sensor_temperature) + ", middle: " + str(middle_sensor_temperature) + ", right: " + str(right_sensor_temperature) + ", tank: " + str(tank_sensor_temperature))
    
    # Set flag indicating enabling/disabling the pump
    pumpEnabled = should_pump_be_enabled(left_sensor_temperature, middle_sensor_temperature, right_sensor_temperature, pump_launching_temperature)     

    r.set('left_sensor_temperature', left_sensor_temperature)
    r.set('middle_sensor_temperature', middle_sensor_temperature)
    r.set('right_sensor_temperature', right_sensor_temperature)    
    r.set('tank_sensor_temperature', tank_sensor_temperature)

    # Additional diagnostics data
    r.set('cpu_usage', psutil.cpu_percent())
    # r.set('cpu_temperature', psutil.cpu_percent())