#!/usr/bin/env python
import psutil
import redis
import time
import threading
# from w1thermsensor import W1ThermSensor
import os.path
import glob
# import RPi.GPIO as GPIO
import sys, os, signal, datetime
import psycopg2

# Establish connection with Redis store
r = redis.Redis(host='localhost', port=6379, db=0)

# Establish connection to Postgresql database
connection = psycopg2.connect(user = "solar", password = os.environ['DBPASSWORD'], host = "127.0.0.1", port = "5432", database = "solar")
cursor = connection.cursor()
insertQuery = "INSERT INTO  webapp_temperature (\"leftSensorTemperature\", \"middleSensorTemperature\", \"rightSensorTemperature\", \"tankSensorTemperature\", \"dateOfReading\") VALUES (%s,%s,%s,%s,%s)"

global pumpEnabled
pumpEnabled = False

mode = '' # Decides if app should run in production mode (on Raspberry PI hardware) or in development mode (machines without real, but mocked GPIO, sensors etc)
startTime = int(time.time()) # Get application start time

# This helper is used to convert booleans from database read as a string to Pythons' bool type
def str_to_bool(s):
    s = s.decode('utf-8')
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError

# Setup initial data into Redis, if they are not defined there
def initialSetup():
    automaticControl = r.get('automaticControl')
    manualControl = r.get('manualControl')
    pumpLaunchingTemperature = r.get('pumpLaunchingTemperature')
    pumpWorkingTime = r.get('pumpWorkingTime')
    temperatureReadInterval = r.get('temperatureReadInterval')
    prodMode = r.get('prodMode')
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
    global mode
    if not prodMode:
        mode = True
        r.set('prodMode', 'True')
    else:
    	mode = str_to_bool(prodMode)

# Enables pump for specific amount of time in new thread
def enable_pump():
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
            # print("Pump state: ON")
            if GPIO.input(11): # Ensure that pump is already stopped
                GPIO.output(11, GPIO.LOW) # Enable power for pump
        if (not pumpEnabled and not str_to_bool(r.get('manualControl'))) and (currentRun - lastTimePumpDisabled > 10) and (currentRun - lastTimePumpEnabled > 10) and previousState: # This condition is as follows: if pump should be disabled according to automatic mode and manual mode
            lastTimePumpDisabled = int(time.time())
            previousState = False
            r.set('pump_state', 0) # Save to database, that pump is disabled
            # print("Pump state: OFF")
            if not GPIO.input(11): # Ensure that pump is already running
                GPIO.output(11, GPIO.HIGH) # Disable power for pump

# Reads temperatures from sensors in its own thread
def read_temperature_from_sensors():
    t = threading.currentThread()
    lastSave = 0
    while getattr(t, "should_still_be_running", True):
        time.sleep(0.1)
        # Read temperature from the left sensor
        try:
            r.set('left_sensor_temperature', W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "0301977967aa").get_temperature())
        except:
            r.set('left_sensor_temperature', "Czujnik prawy nie odpowiada!")
            resetW1()
        # Read temperatures from the middle sensor
        try:
            r.set('middle_sensor_temperature', W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "030797798ac5").get_temperature())
        except:
            r.set('middle_sensor_temperature', "Czujnik środkowy nie odpowiada!")
            resetW1()
        # Read temperatures from the right sensor
        try:
            r.set('right_sensor_temperature', W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "030797793bcd").get_temperature())
        except:
            r.set('right_sensor_temperature', "Czujnik prawy nie odpowiada!")
            resetW1()
        # Read temperatures from water heat tank
        try:
            r.set('tank_sensor_temperature', W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "03019779181c").get_temperature())
        except:
            r.set('tank_sensor_temperature', "Czujnik w zbiorniku nie odpowiada!")
            resetW1()
        # Save temperatures to database once per every even minutes
        if datetime.datetime.now().minute % 2 == 0 and (int(time.time()) - lastSave > 60):
            lastSave = int(time.time())
            cursor.execute(insertQuery, (isNumber(r.get('left_sensor_temperature')), isNumber(r.get('middle_sensor_temperature')), isNumber(r.get('right_sensor_temperature')), isNumber(r.get('tank_sensor_temperature')), datetime.datetime.now()))
            connection.commit()

# Reset sensors using hardware relay (for data line) and manageable GPIO pin (for power line)
def resetW1():
    # Don't disable power earlier than 2 minutes (120 seconds) after application boot:
    if int(time.time()) - startTime > 120:
        GPIO.output(12, GPIO.LOW) # disable power line for sensors
        GPIO.output(13, GPIO.LOW) # disable data line for sensors
        time.sleep(5) # cut off the power from sensors for 15 seconds to let them reset
        GPIO.output(13, GPIO.HIGH) # enable data line for sensors again
        GPIO.output(12, GPIO.HIGH) # enable power line for sensors again
        time.sleep(5)
   
# Decides if pump should be enabled
def should_pump_be_enabled(left, middle, right, launching):
    return (left >= launching or middle >= launching or right >= launching) and str_to_bool(r.get('automaticControl')) # Check, if pump should be launched depending on temperature measurement and only in automatic mode pump can be enabled automatically

def isNumber(item):
    try:
        return float(item)
    except ValueError:
        return -1000

# Return CPU temperature as a character string
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))

# Handler for stopping/killing application gracefully
def handleStopSignalsOrKeyboardInterrupt(thread, temperatureThread):
    thread.should_still_be_running = False
    temperatureThread.should_still_be_running = False
    thread.join()
    temperatureThread.join()
    print("Pump thread state (False = disabled, True: enabled):  " + str(thread.isAlive()))
    print("Temperature sensors thread state (False = disabled, True: enabled):  " + str(temperatureThread.isAlive()))
    print()

# ---------------------------------------------------------------
# ---------------------------------------------------------------
# ---------------------------------------------------------------
#
# Start executing script
initialSetup()

# It is not possible to connect i.e. temperature sensors to the development machine, so that we must run script with parameters determining if script should run in real (production) mode or in development mode (with mocked temperature sensors, mocked pump control etc)
if mode:
    print('Started backend in PRODUCTION mode')
    # Import and configure Raspberry PI specific libraries
    from w1thermsensor import W1ThermSensor
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(12, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(13, GPIO.OUT, initial=GPIO.HIGH)

    # Launch new thread for pump control
    thread = threading.Thread(target=enable_pump, args=())
    thread.should_still_be_running = True
    thread.start()
    # Launch new thread for reading temperatures
    temperatureThread = threading.Thread(target=read_temperature_from_sensors, args=())
    temperatureThread.should_still_be_running = True
    temperatureThread.start()

    signal.signal(signal.SIGTERM, handleStopSignalsOrKeyboardInterrupt)
    signal.signal(signal.SIGTSTP, handleStopSignalsOrKeyboardInterrupt)
    signal.signal(signal.SIGHUP, handleStopSignalsOrKeyboardInterrupt)
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
        handleStopSignalsOrKeyboardInterrupt(thread, temperatureThread)
    except Exception:
        handleStopSignalsOrKeyboardInterrupt(thread, temperatureThread)
        print("Unknown error!")
    finally:
        GPIO.cleanup()
else:
    import developerApp as da
    print('Started backend in DEVELOPMENT mode')
    da.runDevelopmentBackend(r, connection, cursor, insertQuery)
# Close connection to PostgreSQL database
if connection:
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")
print("Script ended successfully!")
sys.exit(0)
