from django import forms

class LoginForm(forms.Form):
    email = forms.CharField(max_length = 100)
    password = forms.CharField(widget = forms.PasswordInput())

class ManagementForm(forms.Form):
    automatic = forms.BooleanField(required=False)
    other = forms.BooleanField(required=False)
    pumpLaunchingTemperature = forms.IntegerField(error_messages={'required': 'Wprowadź temperaturę włączenia pompki (przywrócono poprzednią wartość)', 'max_value': 'Temperatura włączenia pompki musi być z zakresu 0-100 stopni Celsjusza', 'min_value': 'Temperatura włączenia pompki musi być z zakresu 0-100 stopni Celsjusza'}, required=True, min_value = 0, max_value=100)
    pumpTime = forms.IntegerField(error_messages={'required': 'Wprowadź czas działana pompki (przywrócono poprzednią wartość)', 'max_value': 'Czas działania pompki musi być z zakresu 0-300 sekund', 'min_value': 'Czas działania pompki musi być z zakresu 0-300 sekund'}, required=True, min_value = 0, max_value=300)
    interval = forms.IntegerField(error_messages={'required': 'Wprowadź interwał odczytu temperatury (przywrócono poprzednią wartość)', 'max_value': 'Czas interwału musi być z zakresu 0-300 sekund', 'min_value': 'Czas interwału musi być z zakresu 0-300 sekund'}, required=True, min_value = 0, max_value=300)