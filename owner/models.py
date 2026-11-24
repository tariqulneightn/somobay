from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.db.models.expressions import F
from django.db.models.fields import NullBooleanField
from django.urls import reverse
from employee.models import Employees

import datetime
import os






