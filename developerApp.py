# This program is for development use only!
# For production please use collector.py with mode PRODUCTION enabled!
import random
import threading
import time
import datetime
import psutil
import redis
import sys, os, signal

pumpEnabled = False
# Enables pump for specific amount of time in new thread
def enable_pump_dev_mode():
    currentRun = lastTimePumpEnabled = 0 #  lastTimePumpEnabled - remember, when pump was last time enabled - it can change state at least 10s from previous state change.
    lastTimePumpDisabled = int(time.time())
    previousState = False # Initial state of the pump (False = pump disabled, True = pump enabled)
    r.set('pump_state', 0) # This prevents from errors if script was terminated during pump is working
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
            pauseAfterPumpStateChange(True)
        if (not pumpEnabled and not str_to_bool(r.get('manualControl'))) and (currentRun - lastTimePumpDisabled > 10) and (currentRun - lastTimePumpEnabled > 10) and previousState: # This condition is as follows: if pump should be disabled according to automatic mode and manual mode
            lastTimePumpDisabled = int(time.time())
            previousState = False
            r.set('pump_state', 0) # Save to database, that pump is disabled
            print("Pump state: OFF")
            pauseAfterPumpStateChange(False)

# Pause pump thread after pump state change (after pump was enabled or disabled)
def pauseAfterPumpStateChange(stateChange): # stateChange: true means pump was enabled, False means pump was disabled
    if stateChange: # Pause pump thread when pump was enabled
        manualControl = str_to_bool(r.get('manualControl'))
        if manualControl:
            print("Pump launched manually")
            time.sleep(10)            
            return
        print("Pump launched automatically")
        pumpWorkingTime = isNumber(r.get('pumpWorkingTime'))
        if pumpWorkingTime > 10:
            time.sleep(pumpWorkingTime)
        else:
            time.sleep(10)    
    else: # Pause pump thread when pump was disabled
        time.sleep(10)
# Reads temperatures from sensors in its own thread
def read_temperature_from_sensors_dev_mode():
    t = threading.currentThread()
    lastSave = 0
    while getattr(t, "should_still_be_running", True):
        time.sleep(2)
        # Read temperature from the left sensor
        try:
            r.set('left_sensor_temperature', round(random.uniform(1, 100), 2))
        except:
            r.set('left_sensor_temperature', "Czujnik prawy nie odpowiada!")
        # Read temperatures from the middle sensor
        try:
            r.set('middle_sensor_temperature', round(random.uniform(1, 100), 2))
        except:
            r.set('middle_sensor_temperature', "Czujnik środkowy nie odpowiada!")
        # Read temperatures from the right sensor
        try:
            r.set('right_sensor_temperature', round(random.uniform(1, 100), 2))
        except:
            r.set('right_sensor_temperature', "Czujnik prawy nie odpowiada!")
        # Read temperatures from water heat tank
        try:
            r.set('tank_sensor_temperature', round(random.uniform(1, 100), 2))
        except:
            r.set('tank_sensor_temperature', "Czujnik w zbiorniku nie odpowiada!")
        date = datetime.datetime
        
        # Save temperatures to database once per every 5 minutes 
        if date.now().minute % 1 == 0 and (int(time.time()) - lastSave > 60): # Save measurement every five minutes and save one measurement minute, whichc is modulo 5
            lastSave = int(time.time())
            cursor.execute(insertQuery, (float(r.get('left_sensor_temperature')), float(r.get('middle_sensor_temperature')), float(r.get('right_sensor_temperature')), float(r.get('tank_sensor_temperature')), datetime.datetime.now()))
            p.commit()

# Handler for stopping/killing application gracefully
def handleStopSignalsOrKeyboardInterrupt(thread, temperatureThread):
    thread.should_still_be_running = False
    temperatureThread.should_still_be_running = False
    thread.join()
    temperatureThread.join()
    print("Pump thread state (False = disabled, True: enabled):  " + str(thread.isAlive()))
    print("Temperature sensors thread state (False = disabled, True: enabled):  " + str(temperatureThread.isAlive()))
    print()
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
# Run instance of backend designed for development computer (which means a backend with mocked temperature sensors and mocked pump control)
def runDevelopmentBackend(redis, postgres, cur, query):
    global r, p, cursor, insertQuery
    r = redis
    p = postgres
    cursor = cur
    insertQuery = query
    # Launch new thread for pump control
    thread = threading.Thread(target=enable_pump_dev_mode, args=())
    thread.should_still_be_running = True
    thread.start()
    # Launch new thread for reading temperatures
    temperatureThread = threading.Thread(target=read_temperature_from_sensors_dev_mode, args=())
    temperatureThread.should_still_be_running = True
    temperatureThread.start()
    signal.signal(signal.SIGTERM, handleStopSignalsOrKeyboardInterrupt)
    signal.signal(signal.SIGTSTP, handleStopSignalsOrKeyboardInterrupt)
    signal.signal(signal.SIGHUP, handleStopSignalsOrKeyboardInterrupt)
    global pumpEnabled
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
            r.set('cpu_temperature', round(random.uniform(40, 50), 2))
    except KeyboardInterrupt:
        handleStopSignalsOrKeyboardInterrupt(thread, temperatureThread)
    except Exception:
        handleStopSignalsOrKeyboardInterrupt(thread, temperatureThread)
        print("Unknown error!")