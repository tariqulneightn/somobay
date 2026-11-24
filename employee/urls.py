from django.contrib import admin
from django.urls import path,re_path, include

from django.conf.urls import url
from employee.views import *
from owner.views import loanReturnEntry, savingsEntry, withdrawEntry,newLoanEntry
app_name = 'employee'

urlpatterns = [
    
    path('all-client/', employeeDashboard, name='all_client'),
    path('add-client/', addClient, name='add_client'),
    path('client-details/<int:id>', clientDetails, name='client_details'),
    path('search-client/', searchClient, name='search_client'),


    path('loan-return-entry/<int:id>', loanReturnEntry, name='loan-return-entry'),
    # path('new-loan-entry/<int:id>', newLoanEntry, name='new-loan-entry'),
    path('saving-entry/<int:id>', savingsEntry, name='saving-entry'),
    path('withdraw-entry/<int:id>', withdrawEntry, name='withdraw-entry'), 
    path('new-loan-entry/<int:id>', newLoanEntry, name='new_loan_entry')

    # path('super-admin-register/', SuperAdminRegistrationView.as_view(), name='super_admin_register'),
]