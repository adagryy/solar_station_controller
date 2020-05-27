from django.shortcuts import render, redirect
from django.urls import reverse
from .formsDefinition.forms import LoginForm, ManagementForm
import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import redis
from datetime import datetime, timedelta
from .models import Temperature
import json
from django.core.serializers.json import DjangoJSONEncoder

# Get an instance of a logger
logger = logging.getLogger(__name__)

@login_required
def chartData(request):
    time_threshold = datetime.now() - timedelta(hours=24)
    result = list(Temperature.objects.filter(dateOfReading__gt=time_threshold).order_by('dateOfReading').values())
    return HttpResponse(json.dumps(result, sort_keys=True, indent=1, cls=DjangoJSONEncoder))

@login_required
def parameters(request):
    return render(request, 'viewer/parameters.html', {})	

@login_required
def mirrormanagement(request):
    redisDbReference = redis.Redis(host='localhost', port=6379, db=0)
    if request.method == 'POST':
        managementData = ManagementForm(request.POST)
        if managementData.is_valid():
            print("sdfdsafsda: " + str(managementData.cleaned_data['dynamicThresholdControl']))
            redisDbReference.set('automaticControl', str(managementData.cleaned_data['automaticControl']))
            redisDbReference.set('manualControl', str(managementData.cleaned_data['manualControl']))
            redisDbReference.set('dynamicThresholdControl', str(managementData.cleaned_data['dynamicThresholdControl']))
            redisDbReference.set('pumpLaunchingTemperature', managementData.cleaned_data['pumpLaunchingTemperature'])        
            redisDbReference.set('pumpWorkingTime', managementData.cleaned_data['pumpWorkingTime'])
            redisDbReference.set('temperatureReadInterval', managementData.cleaned_data['temperatureReadInterval'])
            redisDbReference.set('dynamicLaunchingTemperature', managementData.cleaned_data['dynamicLaunchingTemperature'])
            
            return render(request, 'management/management.html', {'form': managementData, 'automaticControl': str_to_bool(redisDbReference.get('automaticControl')), 'manualControl': str_to_bool(redisDbReference.get('manualControl')),'dynamicThresholdControl': str_to_bool(redisDbReference.get('dynamicThresholdControl')),'pumpLaunchingTemperature': int(redisDbReference.get('pumpLaunchingTemperature') or "-1"), 'pumpWorkingTime': int(redisDbReference.get('pumpWorkingTime') or "-1"), 'temperatureReadInterval': int(redisDbReference.get('temperatureReadInterval') or "-1"), 'dynamicLaunchingTemperature': int(redisDbReference.get('dynamicLaunchingTemperature') or "-1")})
        else:
            return render(request, 'management/management.html', {'form': managementData, 'automaticControl': str_to_bool(redisDbReference.get('automaticControl')), 'manualControl': str_to_bool(redisDbReference.get('manualControl')),'dynamicThresholdControl': str_to_bool(redisDbReference.get('dynamicThresholdControl')),'pumpLaunchingTemperature': int(redisDbReference.get('pumpLaunchingTemperature') or "-1"), 'pumpWorkingTime': int(redisDbReference.get('pumpWorkingTime') or "-1"), 'temperatureReadInterval': int(redisDbReference.get('temperatureReadInterval') or "-1"), 'dynamicLaunchingTemperature': int(redisDbReference.get('dynamicLaunchingTemperature') or "-1")})
    elif request.method == 'GET':
        return render(request, 'management/management.html', {'automaticControl': str_to_bool(redisDbReference.get('automaticControl')), 'manualControl': str_to_bool(redisDbReference.get('manualControl')),'dynamicThresholdControl': str_to_bool(redisDbReference.get('dynamicThresholdControl')),'pumpLaunchingTemperature': int(redisDbReference.get('pumpLaunchingTemperature') or "-1"), 'pumpWorkingTime': int(redisDbReference.get('pumpWorkingTime') or "-1"), 'temperatureReadInterval': int(redisDbReference.get('temperatureReadInterval') or "-1"), 'dynamicLaunchingTemperature': int(redisDbReference.get('dynamicLaunchingTemperature') or "-1")})
    # What now?
    # return render(request, 'management/management.html', {})

def str_to_bool(s):
    s = s or b'False'
    s = s.decode('utf-8')
    if s == 'True':
         return True
    elif s == 'False':
         return False
    else:
         raise ValueError 

# --------------------
# User authentication
# --------------------
def index(request):
    return render(request, 'viewer/index.html', {}) 
def mainView(request):    
    return render(request, 'viewer/index.html', {})
def login_user(request):
    shouldDisableLoginButton = True
    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'shouldDisableLoginButton': shouldDisableLoginButton})
    if request.method == 'POST':
        MyLoginForm = LoginForm(request.POST) 
        if MyLoginForm.is_valid():
        	# Read data from login form
            emailFromForm = MyLoginForm.cleaned_data['email']
            passwordFromForm = MyLoginForm.cleaned_data['password']
            # Check, if user was exists in database
            if not User.objects.filter(email=emailFromForm).exists():
            	# If user was not found, then...
                return render(request, 'accounts/login.html', {'shouldDisableLoginButton': shouldDisableLoginButton, 'error': 'Błędne dane logowania.'})
                        # We are looking for a user in database by email
            # Get user data (get username)                        
            databaseuser = User.objects.get(email=emailFromForm)
            logger.info("Found user in database: " + databaseuser.username)
            # Try to authenticate user and his password
            authenticatedUser = authenticate(username=databaseuser.username, password=passwordFromForm)            	         
            if authenticatedUser is not None:
                logger.info("User authenticated: " + str(authenticatedUser))	
                login(request, authenticatedUser)
                return redirect(reverse('mainView'))
            else:
                return render(request, 'accounts/login.html', {'shouldDisableLoginButton': shouldDisableLoginButton, 'error': 'Błędne dane logowania.'})
        else:
            logger.info("not valid")	
            return render(request, 'accounts/login.html', {'shouldDisableLoginButton': shouldDisableLoginButton, 'error': 'Niepoprawnie wprowadzono dane do formularza logowania.'})

def logout_user(request):
    logout(request)
    return redirect(reverse('mainView'))