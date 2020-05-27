from django import forms

class LoginForm(forms.Form):
    email = forms.CharField(max_length = 100)
    password = forms.CharField(widget = forms.PasswordInput())

class ManagementForm(forms.Form):
    automaticControl = forms.BooleanField(required=False)
    manualControl = forms.BooleanField(required=False)
    dynamicThresholdControl = forms.BooleanField(required=False)
    pumpLaunchingTemperature = forms.IntegerField(error_messages={'required': 'Wprowadź temperaturę włączenia pompki (przywrócono poprzednią wartość)', 'max_value': 'Temperatura włączenia pompki musi być z zakresu 0-100 stopni Celsjusza', 'min_value': 'Temperatura włączenia pompki musi być z zakresu 0-100 stopni Celsjusza'}, required=True, min_value = 0, max_value=100)
    pumpWorkingTime = forms.IntegerField(error_messages={'required': 'Wprowadź czas działana pompki (przywrócono poprzednią wartość)', 'max_value': 'Czas działania pompki musi być z zakresu 10-300 sekund', 'min_value': 'Czas działania pompki musi być z zakresu 10-300 sekund'}, required=True, min_value = 10, max_value=300)
    temperatureReadInterval = forms.IntegerField(error_messages={'required': 'Wprowadź interwał odczytu temperatury (przywrócono poprzednią wartość)', 'max_value': 'Czas interwału musi być z zakresu 0-5 sekund', 'min_value': 'Czas interwału musi być z zakresu 0-5 sekund'}, required=True, min_value = 0, max_value=5)
    dynamicLaunchingTemperature = forms.IntegerField(error_messages={'required': 'Wprowadź liczbę o jaką większa ma być temperatura absorbera niż w zbiorniku, aby pompa mogła się uruchomić', 'max_value': 'Zakres ten musi być z przedziału 10-40 stopni', 'min_value': 'Zakres ten musi być z przedziału 10-40 stopni'}, required=True, min_value = 10, max_value=40)