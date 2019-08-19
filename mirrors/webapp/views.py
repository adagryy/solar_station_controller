from django.shortcuts import render, redirect
from django.urls import reverse
from .formsDefinition.forms import LoginForm, ManagementForm
import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import redis

# Get an instance of a logger
logger = logging.getLogger(__name__)

@login_required
def parameters(request):
    return render(request, 'viewer/parameters.html', {})	

@login_required
def mirrormanagement(request):
    redisDbReference = redis.Redis(host='localhost', port=6379, db=0)
    if request.method == 'POST':
        managementData = ManagementForm(request.POST)
        if managementData.is_valid():
            redisDbReference.set('automatic', str(managementData.cleaned_data['automatic']))
            redisDbReference.set('other', str(managementData.cleaned_data['other']))         
            redisDbReference.set('pumpTime', managementData.cleaned_data['pumpTime'])
            redisDbReference.set('interval', managementData.cleaned_data['interval'])
            logger.error('Odczy34t: ' + str(managementData.cleaned_data['automatic']))
            logger.error('Odczyt: ' + str(managementData.cleaned_data['other']))
            logger.error('Odczyt: ' + str(redisDbReference.get('automatic')))
            logger.error('Odczyt: ' + str(redisDbReference.get('other')))
            return render(request, 'management/management.html', {'form': managementData, 'automatic': str_to_bool(redisDbReference.get('automatic')), 'other': str_to_bool(redisDbReference.get('other')), 'pumpTime': int(redisDbReference.get('pumpTime')), 'interval': int(redisDbReference.get('interval'))})
        else:
            return render(request, 'management/management.html', {'form': managementData, 'automatic': str_to_bool(redisDbReference.get('automatic')), 'other': str_to_bool(redisDbReference.get('other')), 'pumpTime': int(redisDbReference.get('pumpTime')), 'interval': int(redisDbReference.get('interval'))})
    elif request.method == 'GET':
        logger.error('Odczyt: ' + str(redisDbReference.get('automatic').decode('utf-8')))
        logger.error('Odczyt: ' + str(redisDbReference.get('other').decode('utf-8')))
        return render(request, 'management/management.html', {'automatic': str_to_bool(redisDbReference.get('automatic')), 'other': str_to_bool(redisDbReference.get('other')), 'pumpTime': int(redisDbReference.get('pumpTime')), 'interval': int(redisDbReference.get('interval'))})
    # return render(request, 'management/management.html', {})

def str_to_bool(s):
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