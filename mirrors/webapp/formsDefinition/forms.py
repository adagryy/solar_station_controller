from django import forms

class LoginForm(forms.Form):
    email = forms.CharField(max_length = 100)
    password = forms.CharField(widget = forms.PasswordInput())

class ManagementForm(forms.Form):
    automatic = forms.BooleanField(required=False)
    other = forms.BooleanField(required=False)
    pumpTime = forms.IntegerField(required=True, min_value = 0, max_value=300)
    interval = forms.IntegerField(required=True, min_value = 0, max_value=300)