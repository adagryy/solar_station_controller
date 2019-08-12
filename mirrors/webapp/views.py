from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'viewer/index.html', {}) 
def mainView(request):
	return render(request, 'viewer/index.html', {})
def login(request):
    if request.method == 'GET':
        return render(request, 'viewer/login.html', {})
    if request.method == 'POST':
        return render(request, 'viewer/index.html', {})