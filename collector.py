#!/usr/bin/env python
import psutil
import redis
import time
import threading
from w1thermsensor import W1ThermSensor
import os.path  
import glob
import RPi.GPIO as GPIO
import sys, os

# Establish connection with Redis store
r = redis.Redis(host='localhost', port=6379, db=0)
global pumpEnabled
pumpEnabled = False
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)

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
    previousState = False # Initial state of the pump (False = pump disabled, True = pump enabled)

    t = threading.currentThread()
    while getattr(t, "should_still_be_running", True):
        # Read, how much time pump should be enabled at once
        delay = int(r.get('pumpWorkingTime'))
        time.sleep(0.5)

        currentRun = int(time.time()) # we measure time to compare when pump was last time enabled/disabled to avoid enabling/disabling pump too fast (i.e 3 time per second)

        # Flag saying pump should be enabled
        if (pumpEnabled or str_to_bool(r.get('manualControl'))) and (currentRun - lastTimePumpEnabled > 10) and (currentRun - lastTimePumpDisabled > 10) and not previousState: # This condition is as follows: if pump should be enabled according to automatic mode or manual mode
            lastTimePumpEnabled = int(time.time())
            previousState = True
            r.set('pump_state', 1) # Save to database, that pump is enabled
            print("Pump state: ON")             
            # if gpio.LOW            
            #     enable gpio
            #     sleep(delay)        
        if (not pumpEnabled and not str_to_bool(r.get('manualControl'))) and (currentRun - lastTimePumpDisabled > 10) and (currentRun - lastTimePumpEnabled > 10) and previousState: # This condition is as follows: if pump should be disabled according to automatic mode and manual mode
            lastTimePumpDisabled = int(time.time())
            previousState = False
            r.set('pump_state', 0) # Save to database, that pump is disabled
            print("Pump state: OFF") 
            # if gpio.HIGH 
            #     disable gpio

# Reads temperatures from sensors in its own thread
def read_temperature_from_sensors():
    t = threading.currentThread()
    while getattr(t, "should_still_be_running", True):
        time.sleep(0.1)

        # Read temperature from the left sensor
        try:
            r.set('left_sensor_temperature', W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "030797793bcd").get_temperature())   
        except:
            r.set('left_sensor_temperature', "Czujnik prawy nie odpowiada!")

        # Read temperatures from the middle sensor
        try:
            r.set('middle_sensor_temperature', W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "030797798ac5").get_temperature())
        except:
            r.set('middle_sensor_temperature', "Czujnik środkowy nie odpowiada!")

        # Read temperatures from the right sensor
        try:             
            r.set('right_sensor_temperature', W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "0301977967aa").get_temperature())
        except:
            r.set('right_sensor_temperature', "Czujnik prawy nie odpowiada!")

        # Read temperatures from water heat tank
        # tank_sensor_temperature = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "030797798ac5").get_temperature()

# Method is used for automatic control of temperature sensors, which sometimes are crashing from unknown reason and then must be switched off using relay, and then switched on again
def control_temperature_sensors():
    t = threading.currentThread()
    while getattr(t, "should_still_be_running", True):
        time.sleep(5)
        foldersCount = len(glob.glob("/sys/bus/w1/devices/*"))
        if foldersCount != 4:
            GPIO.output(13, GPIO.HIGH)
            # print("Starting reset sensors: " + str(GPIO.input(13)))
            time.sleep(5)
            GPIO.output(13, GPIO.LOW)
            # print("Ending reset sensors: " + str(GPIO.input(13)))


# Decides if pump should be enabled
def should_pump_be_enabled(left, middle, right, launching):
    return (left >= launching or middle >= launching or right >= launching) and str_to_bool(r.get('automaticControl')) # Check, if pump should be launched depending on temperature measurement and only in automatic mode pump can be enabled automatically

# This helper is used to convert booleans from database read as a string to Pythons' bool type
def str_to_bool(s):
    s = s.decode('utf-8')
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError 

def isNumber(item):
    try:
        return float(item)
    except ValueError:
        return -1000

# Return CPU temperature as a character string                                      
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))

# ---------------------------------------------------------------
# ---------------------------------------------------------------
# ---------------------------------------------------------------

# Start executing script
initialSetup()

# Launch new thread for pump control
thread = threading.Thread(target=enable_pump, args=())
thread.should_still_be_running = True
thread.start()

# Launch new thread for reading temperatures
temperatureThread = threading.Thread(target=read_temperature_from_sensors, args=())
temperatureThread.should_still_be_running = True
temperatureThread.start()

# Launch new thread for controlling when temperature sensors crash
controlThread = threading.Thread(target=control_temperature_sensors, args=())
controlThread.should_still_be_running = True
controlThread.start()

try:
    while True:
        # Reading delay
        time.sleep(int(r.get('temperatureReadInterval')))

        # Get the pump launching temperature; if absorber exceeds this temperature, pump then is launched
        pump_launching_temperature = int(r.get('pumpLaunchingTemperature'))

        # print("temperatureReadInterval: " + strl(int(r.get('temperatureReadInterval'))) + ", launch: " + str(pump_launching_temperature) + ", left: " + str(left_sensor_temperature) + ", middle: " + str(middle_sensor_temperature) + ", right: " + str(right_sensor_temperature) + ", tank: " + str(tank_sensor_temperature))
    
        # Set flag indicating enabling/disabling the pump    
        pumpEnabled = should_pump_be_enabled(isNumber(r.get('left_sensor_temperature')), isNumber(r.get('middle_sensor_temperature')), isNumber(r.get('right_sensor_temperature')), pump_launching_temperature)     

        #### Additional diagnostics data ####
        # Get CPU utilization
        r.set('cpu_usage', psutil.cpu_percent())

        # Get CPU temperature
        r.set('cpu_temperature', getCPUtemperature())
except KeyboardInterrupt:
    thread.should_still_be_running = False
    temperatureThread.should_still_be_running = False
    controlThread.should_still_be_running = False
    thread.join()
    temperatureThread.join()
    controlThread.join()
    print("Pump thread state (False = disabled, True: enabled):  " + str(thread.isAlive()))
    print("Temperature sensors thread state (False = disabled, True: enabled):  " + str(temperatureThread.isAlive()))
    print("Sensors control thread state (False = disabled, True: enabled):  " + str(controlThread.isAlive()))
    print()
except Exception:
    print("Unknown error!")
finally:
    GPIO.cleanup()
print("Script ended successfully!")
sys.exit(0)
