from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

import re
from django.db import models
from django.forms import fields
from django.forms.widgets import DateInput
from account.models import User

from employee.models import Employees
from account.models import User

from django.core.exceptions import ValidationError


class EmployeeRegForm(forms.ModelForm):
    class Meta:
        model= User
        fields= ['first_name', 'email', 'password', 'phone']

        error_messages = {
            'first_name': {
                'required': 'Name is required',
            },
            'email': {
                'required': 'email is required.'
            },
            'password': {
                'required': 'Password is required.'
            },
            'phone': {
                'required': 'Phone is important.'
            },
        }


    def __init__(self, *args, **kwargs):
        super(EmployeeRegForm, self).__init__(*args, **kwargs)
       
        self.fields['phone'].required = True
        self.fields['first_name'].required = True
        self.fields['password'].required = True

    def clean_phone(self, *args, **kwargs):
        phone = self.cleaned_data.get('phone')
        if len(phone) < 11:
            raise forms.ValidationError("phone number is too short")
        elif re.search('[a-zA-Z]', phone):
            raise forms.ValidationError("Invalid phone number")
        else:
            return phone

class EmployeeDetailsForm(forms.ModelForm):
    class Meta:
        model= Employees
        fields= ['fathers_name', 'birthdate', 'nid', 'present_address', 'permanent_address', 'designation']
        error_messages = {
            
            'nid': {
                'required': 'NID is required.'
            },
            'present_address': {
                'required': 'Present Address is required.'
            },
            
        }

    def __init__(self, *args, **kwargs):
        super(EmployeeDetailsForm, self).__init__(*args, **kwargs)

        self.fields['nid'].required = True
        self.fields['present_address'].required = True
