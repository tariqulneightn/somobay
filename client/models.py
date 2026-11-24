from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from employee.models import Employees

import datetime
import os



class Clients(models.Model):
    employee_for = models.ForeignKey(Employees, on_delete=models.CASCADE)
    membership_no = models.CharField(max_length=30, null=False, blank=False, default='')
    name = models.CharField(max_length=30, null=False, blank=False, default='')
    fathers_name = models.CharField(max_length=30, null=False, blank=False, default='')
    birthdate = models.DateField(null=False, blank=False)
    nid = models.CharField(max_length=20, null=False, blank=False, default='')
    phone = models.CharField(max_length=50, blank=False, null=False, default='')
    present_address = models.CharField(max_length=100, blank=False, null=False, default='')
    business_address = models.CharField(max_length=100, blank=False, null=False, default='')
    business_type = models.CharField(max_length=15, blank=False, null=False, default='')
    loan_amount = models.IntegerField(blank=True, null=True)
    returnable_amount = models.IntegerField(blank=True, null=True)
    loan_giving_date = models.DateField(blank=True, null=True)
    # product = models.CharField(max_length=15, blank=False, null=False, default='')
    taking_loan = models.BooleanField(default=False)
    saving_money = models.BooleanField(default=False)
    loan_return_period = models.IntegerField(blank=True, null=True)
    register_date = models.DateField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __int__(self):
        return self.id


class LoanReturnDetails(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    loan_return_amount = models.IntegerField(blank=False, null=False)
    loan_return_date = models.DateField()
    total_returned = models.IntegerField(blank=True, null=True, default=0)
    remaining_loan = models.IntegerField(blank=True, null=True, default=0)
    employee = models.ForeignKey(Employees, blank=True, null=True, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)

    def __int__(self):
        return self.id

class SavingDetails(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    saving_amount = models.IntegerField(blank=False, null=False, default=0)
    saving_date = models.DateField(blank=True, null=True)
    total_savings = models.IntegerField(blank=True, null=True, default=0)
    withdraw_amount = models.IntegerField(blank=False, null=False, default=0)
    withdraw_date = models.DateField(blank=True, null=True)
    total_withdraw = models.IntegerField(blank=True, null=True, default=0)
    remaining_saving = models.IntegerField(blank=True, null=True, default=0)
    employee = models.ForeignKey(Employees, blank=True, null=True, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)

    def __int__(self):
        return self.id


class ProductDetails(models.Model):
    product_name = models.CharField(max_length=20, blank=True, null=True, default='')
    quantity = models.IntegerField(blank=True, null=True, default=0)
    unite_price = models.IntegerField(blank=True, null=True, default=0)
    total_price = models.IntegerField(blank=True, null=True, default=0)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)