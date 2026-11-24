from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.urls import reverse


import datetime
import os

from account.models import User


class Employees(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # name = models.CharField(max_length=30, null=False, blank=False, default='')
    fathers_name = models.CharField(max_length=30, null=False, blank=False, default='')
    birthdate = models.DateField(null=False, blank=False)
    nid = models.CharField(max_length=20, null=False, blank=False, default='')
    # phone = models.CharField(max_length=16, blank=False, null=False, default='')
    present_address = models.CharField(max_length=100, blank=False, null=False, default='')
    permanent_address = models.CharField(max_length=100, blank=False, null=False, default='')
    designation = models.CharField(max_length=30, blank=True, null=True, default='')
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __int__(self):
        return self.id
