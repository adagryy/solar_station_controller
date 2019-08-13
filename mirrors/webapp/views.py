from django.shortcuts import render, redirect
from django.urls import reverse
from .formsDefinition.forms import LoginForm
import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.
def index(request):
    return render(request, 'viewer/index.html', {}) 
def mainView(request):    
    return render(request, 'viewer/index.html', {})
def login_user(request):
    shouldDisableLoginButton = True
    if request.method == 'GET':
        return render(request, 'viewer/login.html', {'shouldDisableLoginButton': shouldDisableLoginButton})
    if request.method == 'POST':
        MyLoginForm = LoginForm(request.POST) 
        if MyLoginForm.is_valid():
        	# Read data from login form
            emailFromForm = MyLoginForm.cleaned_data['email']
            passwordFromForm = MyLoginForm.cleaned_data['password']
            # Check, if user was exists in database
            if not User.objects.filter(email=emailFromForm).exists():
            	# If user was not found, then...
                return render(request, 'viewer/login.html', {'shouldDisableLoginButton': shouldDisableLoginButton, 'error': 'Błędne dane logowania.'})
                        # We are looking for a user in database by email
            # Get user data (get username)                        
            databaseuser = User.objects.get(email=emailFromForm)
            logger.info("Found user in database: " + databaseuser.username)
            # Try to authenticate user and his password
            authenticatedUser = authenticate(username=databaseuser.username, password=passwordFromForm)            	         
            if authenticatedUser is not None:
                logger.info("User authenticated: " + str(authenticatedUser))	
                login(request, authenticatedUser)
                return redirect(reverse('index'))
            else:
                return render(request, 'viewer/login.html', {'shouldDisableLoginButton': shouldDisableLoginButton, 'error': 'Błędne dane logowania.'})
        else:
            logger.info("not valid")	
            return render(request, 'viewer/login.html', {'shouldDisableLoginButton': shouldDisableLoginButton, 'error': 'Niepoprawnie wprowadzono dane do formularza logowania.'})

def logout_user(request):
    logout(request)
    return redirect(reverse('index'))