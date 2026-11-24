from django.contrib import admin
from django.urls import path,re_path, include

from django.conf.urls import url
from account.views import *
app_name = 'account'

urlpatterns = [
    
    path('login/', LoginView.as_view(), name='login_page'),
    path('logout/', LogoutView.as_view(), name='logout' ),
    # path('super-admin-register/', SuperAdminRegistrationView.as_view(), name='super_admin_register'),
]