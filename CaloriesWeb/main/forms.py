from django import forms
from django.forms import ModelForm, TextInput, PasswordInput
from django.contrib.auth.forms import UserCreationForm

from .models import User

class LogInForm(forms.Form):

    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username',]

        widgets = {
            'username': TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
            'password1': PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}),
            'password2': PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}),
        }