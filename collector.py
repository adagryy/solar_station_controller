#!/usr/bin/env python
import psutil
import redis
import random
import time
import threading
import os.path
import glob
import sys, os, signal, datetime
import psycopg2
from threading import Lock
lock = Lock()

# Establish connection with Redis store
r = redis.Redis(host='localhost', port=6379, db=0)

# Establish connection to Postgresql database
connection = psycopg2.connect(user = "solar", password = os.environ['DBPASSWORD'], host = "127.0.0.1", port = "5432", database = "solar")
cursor = connection.cursor()
insertQuery = "INSERT INTO  webapp_temperature (\"leftSensorTemperature\", \"middleSensorTemperature\", \"rightSensorTemperature\", \"tankSensorTemperature\", \"dateOfReading\") VALUES (%s,%s,%s,%s,%s)"

pumpEnabled = False
pumpState = False

lastSave = 0

runningMode = '' # Decides if app should run in production mode (on Raspberry PI hardware) or in development mode (machines without real, but mocked GPIO, sensors etc)
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
    global runningMode
    automaticControl = r.get('automaticControl')
    manualControl = r.get('manualControl')
    dynamicThresholdControl = r.get('dynamicThresholdControl')
    pumpLaunchingTemperature = r.get('pumpLaunchingTemperature')
    pumpWorkingTime = r.get('pumpWorkingTime')
    temperatureReadInterval = r.get('temperatureReadInterval')
    prodMode = r.get('prodMode')
    dynamicLaunchingTemperature = r.get('dynamicLaunchingTemperature')  # this value shows dynamic threshold of absorber temperature to launch the pump 
                                                                        # in comparison to the temperature of water in tank. 
                                                                        # This only works if "progressiveThresholdControl" is "True"
                                                                        # For example if sensor in water tank shows 30 celsius degree and "dynamicLaunchingTemperature" is set to 27, then pump will launch when one of sensors on absorber will reach the value of 57 (which is 30 + 27)
    if not automaticControl:
        r.set('automaticControl', 'False')
    if not manualControl:
        r.set('manualControl', 'False')
    if not dynamicThresholdControl:
        r.set('dynamicThresholdControl', 'False')
    if not pumpLaunchingTemperature:
        r.set('pumpLaunchingTemperature', '60')
    if not pumpWorkingTime:
        r.set('pumpWorkingTime', '30')
    if not temperatureReadInterval:
        r.set('temperatureReadInterval', '2')
    if not prodMode:
        runningMode = False
        r.set('prodMode', 'False')
    else:
        runningMode = str_to_bool(prodMode)        
    if not dynamicLaunchingTemperature: 
        r.set('dynamicLaunchingTemperature', 20)

# Enables pump for specific amount of time in new thread
def enable_pump():
    currentRun = lastTimePumpEnabled = 0 #  lastTimePumpEnabled - remember, when pump was last time enabled - it can change state at least 10s from previous state change.
    lastTimePumpDisabled = int(time.time())
    previousState = False # Initial state of the pump (False = pump disabled, True = pump enabled)
    global pumpState
    r.set('pump_state', 0) # This prevents from errors if script was terminated during pump is working
    t = threading.currentThread()
    while getattr(t, "should_still_be_running", True):
        # Read, how much time pump should be enabled at once
        time.sleep(0.5)     
        currentRun = int(time.time()) # we measure time to compare when pump was last time enabled/disabled to avoid enabling/disabling pump too fast (i.e 3 time per second)
        # Flag saying pump should be enabled
        if pumpEnabled and (currentRun - lastTimePumpDisabled > 10) and not previousState: # This condition is as follows: if pump should be enabled according to automatic mode or manual mode
            lastTimePumpEnabled = int(time.time())
            previousState = True            
            r.set('pump_state', 1) # Save to database, that pump is enabled
            # print("Pump state: ON")            
            if runningMode:
                # ======================================================== RASPBERRY PI ONLY CODE ========================================================
                if GPIO.input(11): # Ensure that pump is already stopped
                    GPIO.output(11, GPIO.LOW) # Enable electric power for pump
                    pumpState = True
                    pauseAfterPumpStateChange(True)
                # ========================================================================================================================================
            else:
                print("Pump state: ON")
                pumpState = True
                pauseAfterPumpStateChange(True)
        if (not pumpEnabled) and (currentRun - lastTimePumpEnabled > 10) and previousState: # This condition is as follows: if pump should be disabled according to automatic mode and manual mode
            lastTimePumpDisabled = int(time.time())
            previousState = False            
            r.set('pump_state', 0) # Save to database, that pump is disabled            
            if runningMode:
                # ======================================================== RASPBERRY PI ONLY CODE ========================================================
                if not GPIO.input(11): # Ensure that pump is already running
                    GPIO.output(11, GPIO.HIGH) # Disable electric power for pump
                    pumpState = False
                    pauseAfterPumpStateChange(False)                    
                # ========================================================================================================================================
            else:
                print("Pump state: OFF")
                pumpState = False
                pauseAfterPumpStateChange(False)                


# Pause pump thread after pump state change (after pump was enabled or disabled)
def pauseAfterPumpStateChange(stateChange): # stateChange: true means pump was enabled, False means pump was disabled
    if stateChange: # Pause pump thread when pump was enabled
        manualControl = str_to_bool(r.get('manualControl'))
        if manualControl:
            time.sleep(10)
            return
        pumpWorkingTime = isNumber(r.get('pumpWorkingTime'))
        if pumpWorkingTime > 10:
            time.sleep(pumpWorkingTime)
        else:
            time.sleep(10)    
    else: # Pause pump thread when pump was disabled
        time.sleep(10)

# Reads temperatures from sensors in its own thread
def read_temperature_from_sensors():
    t = threading.currentThread()
    while getattr(t, "should_still_be_running", True):
        pauseSensorReadings()       
        # Read temperature from the left sensor       
        try:
            left = getSensorTemperature("030797798ac5")
            r.set('left_sensor_temperature', left)
        except:
            r.set('left_sensor_temperature', "Czujnik lewy nie odpowiada!")
            resetW1()
        # Read temperatures from the middle sensor
        try:
            middle = getSensorTemperature("030797794995")
            r.set('middle_sensor_temperature', middle)
        except:
            r.set('middle_sensor_temperature', "Czujnik środkowy nie odpowiada!")
            resetW1()
        # Read temperatures from the right sensor
        try:
            right = getSensorTemperature("0307977948d5")
            r.set('right_sensor_temperature', right)
        except:
            r.set('right_sensor_temperature', "Czujnik prawy nie odpowiada!")
            resetW1()
        # Read temperatures from water heat tank
        try:
            r.set('tank_sensor_temperature', getSensorTemperature("03019779181c"))
        except:
            r.set('tank_sensor_temperature', "Czujnik w zbiorniku nie odpowiada!")
            resetW1()

        # Save temperatures to database once per every even minutes
        saveTemperaturesToDatabase()

def saveTemperaturesToDatabase():
    moduloInterval = 5 # Save readings to database every 5 minutes
    global lastSave

    # if datetime.datetime.now().hour >= 23 or datetime.datetime.now().hour < 7:
    #     moduloInterval = 30 # ...but at night (23:00 to 7:00) save to database every 30 minutes

    # Save temperatures to database once per every even minutes
    if datetime.datetime.now().minute % moduloInterval == 0 and (int(time.time()) - lastSave > 60):            
        left = isNumber(r.get('left_sensor_temperature'))
        middle = isNumber(r.get('middle_sensor_temperature'))
        right = isNumber(r.get('right_sensor_temperature'))
        tank = isNumber(r.get('tank_sensor_temperature'))
        if left > -1000 and middle > -1000 and right > -1000 and tank > -1000:
            lastSave = int(time.time())
            cursor.execute(insertQuery, (left, middle, right, tank, datetime.datetime.now()))
            connection.commit()

def pauseSensorReadings():
    currentHour = datetime.datetime.now().hour
    if currentHour >= 7 and currentHour <= 23:
        time.sleep(int(r.get('temperatureReadInterval')))
    else:
        time.sleep(240) # During night pause readings for 240 seconds

def getSensorTemperature(sensorId):
    if runningMode:
        # ======================================================== RASPBERRY PI ONLY CODE ========================================================
        return W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, sensorId).get_temperature() # Return real temperature from sensor when running on Raspberry PI hardware.
        # ========================================================================================================================================
    else:
        return gen.__next__() # Return generator value representing temperature when running on other server without sensors even attached.

def generateMockTemperature():
    i = int(r.get('pumpLaunchingTemperature')) - 3
    while i < int(r.get('pumpLaunchingTemperature')) + 2:
        if int(round(i)) == int(r.get('pumpLaunchingTemperature')) + 1:
            i = int(r.get('pumpLaunchingTemperature')) - 3
        i += 0.02
        yield int(round(i))       

# Reset sensors using hardware relay (for data line) and manageable GPIO pin (for power line)
def resetW1():
    # Don't disable power earlier than 2 minutes (120 seconds) after application boot:
    if runningMode and int(time.time()) - startTime > 120:
        # ======================================================== RASPBERRY PI ONLY CODE ========================================================
        GPIO.output(12, GPIO.LOW) # disable power line for sensors
        GPIO.output(13, GPIO.LOW) # disable data line for sensors
        time.sleep(5) # cut off the power from sensors for 15 seconds to let them reset
        GPIO.output(13, GPIO.HIGH) # enable data line for sensors again
        GPIO.output(12, GPIO.HIGH) # enable power line for sensors again
        time.sleep(5)
        # ========================================================================================================================================
   
# Decides if pump should be enabled
def should_pump_be_enabled(left, middle, right, launching):    
    if str_to_bool(r.get('manualControl')):
        return True;

    currentHour = datetime.datetime.now().hour # During night pump should be definitely disabled
    if currentHour >= 17 and currentHour <= 9:
        return False 

    if str_to_bool(r.get('automaticControl')):
        return (left >= launching or middle >= launching or right >= launching) # Check, if pump should be launched depending on temperature measurement and only in automatic mode pump can be enabled automatically
            
    if str_to_bool(r.get('dynamicThresholdControl')):
        tankTemperature = int(isNumber(r.get('tank_sensor_temperature')))
        if tankTemperature == -1000:
            return False
        thresholdValue = tankTemperature + int(r.get('dynamicLaunchingTemperature')) # Find dynamically temperature by which the pump is launched (for example run pump, when the absorber heats 20 Celsius degree more than the water temperature in tank)
        return left >= thresholdValue or middle >= thresholdValue or right >= thresholdValue or (left >= launching or middle >= launching or right >= launching)

def isNumber(item):
    try:
        return float(item)
    except ValueError:
        return -1000

# Return CPU temperature as a character string
def getCPUtemperature():
    # vcgencmd is a command line utility that can get various pieces of information from the VideoCore GPU on the Raspberry Pi.
    # So it is only available on Raspberry PI hardware
    if runningMode:
        # ======================================================== RASPBERRY PI ONLY CODE ========================================================
        res = os.popen('vcgencmd measure_temp').readline()
        return(res.replace("temp=","").replace("'C\n",""))
        # ========================================================================================================================================
    else:
        return round(random.uniform(40, 50), 2) # Get random CPU temperature to return back to frontend

# Handler for stopping/killing application gracefully
def handleStopSignalsOrKeyboardInterrupt(thread, temperatureThread):
    thread.should_still_be_running = False
    temperatureThread.should_still_be_running = False
    thread.join()
    temperatureThread.join()
    print("Pump thread state (False = disabled, True: enabled):  " + str(thread.is_alive()))
    print("Temperature sensors thread state (False = disabled, True: enabled):  " + str(temperatureThread.is_alive()))
    print()

# ---------------------------------------------------------------
# ---------------------------------------------------------------
# ---------------------------------------------------------------
#
# Start executing script
initialSetup()

# It is not possible to connect i.e. temperature sensors to the development machine, so that we must run script with parameters determining if script should run in real (production) mode or in development mode (with mocked temperature sensors, mocked pump control etc)
if runningMode:
    print('Started backend in PRODUCTION mode')
    # ======================================================== RASPBERRY PI ONLY CODE ========================================================
    # Import and configure Raspberry PI specific libraries
    from w1thermsensor import W1ThermSensor
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(12, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(13, GPIO.OUT, initial=GPIO.HIGH)
    # ========================================================================================================================================
else:
    print('Started backend in DEVELOPMENT mode')
    gen = generateMockTemperature() # Generate mock temperature
    print(isNumber(r.get('tank_sensor_temperature')))
    print(isNumber(r.get('tank_sensor_temperature')) + int(r.get('dynamicLaunchingTemperature')))

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
        time.sleep(1)

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
except Exception as exception:
    handleStopSignalsOrKeyboardInterrupt(thread, temperatureThread)
    print(exception)
    print("Unknown error!")
finally:
    if runningMode:
        # ======================================================== RASPBERRY PI ONLY CODE ========================================================
        GPIO.cleanup()
        # ========================================================================================================================================

# Close connection to PostgreSQL database
if connection:
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")
print("Script ended successfully!")
sys.exit(0)
