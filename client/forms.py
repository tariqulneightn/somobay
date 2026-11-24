from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

from django.forms.widgets import DateInput
import re

from client.models import Clients, LoanReturnDetails, SavingDetails

class ClientCreateForm(forms.ModelForm):
    class Meta:
        model= Clients
        fields= ['membership_no', 'name', 'fathers_name', 'birthdate', 'nid', 'phone', 'present_address', 'business_address', 'business_type',
                'loan_amount', 'returnable_amount', 'loan_giving_date', 'employee_for', 'taking_loan', 'saving_money', 'loan_return_period', 'register_date']

        error_messages = {
            'name': {
                'required': 'Name is required',
            },
            'membership_no': {
                'required': 'membership_no is required.'
            },
            'fathers_name': {
                'required': 'fathers_name is required.'
            },
            'phone': {
                'required': 'Phone is important.'
            },
            'birthdate': {
                'required': 'birth date is required',
            },
            'nid': {
                'required': 'nid is required.'
            },
            'present_address': {
                'required': 'present_address is required.'
            },
            'business_address': {
                'required': 'business_address is important.'
            },
            'business_type': {
                'required': 'business_type date is required',
            },
            # 'loan_amount': {
            #     'required': 'loan_amount is required.'
            # },
            # 'product': {
            #     'required': 'product is required.'
            # },
            # 'taking_loan': {
            #     'required': 'taking_loan is important.'
            # },
            # 'saving_money': {
            #     'required': 'saving_money is required.'
            # },
            # 'loan_return_period': {
            #     'required': 'loan_return_period is important.'
            # },
        }


    def __init__(self, *args, **kwargs):
        super(ClientCreateForm, self).__init__(*args, **kwargs)
       
        self.fields['membership_no'].required = True
        self.fields['name'].required = True
        self.fields['fathers_name'].required = True
        self.fields['birthdate'].required = True
        self.fields['nid'].required = True
        self.fields['phone'].required = True
        self.fields['present_address'].required = True
        self.fields['business_address'].required = True
        self.fields['business_type'].required = True
        # self.fields['loan_amount'].required = True
        # self.fields['product'].required = True
        # self.fields['taking_loan'].required = True
        # self.fields['saving_money'].required = True
        # self.fields['loan_return_period'].required = True

    # def clean_phone(self, *args, **kwargs):
    #     phone = self.cleaned_data.get('phone')
    #     if len(phone) < 11:
    #         raise forms.ValidationError("phone number is too short")
    #     elif re.search('[a-zA-Z]', phone):
    #         raise forms.ValidationError("Invalid phone number")
    #     else:
    #         return phone