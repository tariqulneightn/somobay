from re import search
from django.contrib import admin
from django.urls import path,re_path, include

from django.conf.urls import url
from owner.views import *
app_name = 'owner'

urlpatterns = [
    
    path('all-client/', ownerDashboard, name='all_client'),
    path('running-client', runningClient, name='running_client'),
    path('expired-client', expiredClient, name='expired_client'), # url for date-over client(date over but haven't returned total loan)
    path('delete-client/<int:id>', removeClient, name='remove_client'),
    path('add-client/', addClient, name='add_client'),
    path('search-client/', searchClient, name='search_client'),
    path('edit-client/<int:id>', editClient, name='edit_client'),
    path('all-employee/', employeeList, name='all_employee'),
    path('delete-employee/<int:id>', removeEmployee, name='remove_employee'),
    path('activate-employee/<int:id>', activateEmployee, name='activete_employee'),
    path('add-employee/', addEmployee, name='add_employee'),
    path('edit-employee/<int:id>', editEmployee, name='edit_employee'),
    path('client-details/<int:id>', clientDetails, name='client_details'),

    path('loan-return-entry/<int:id>', loanReturnEntry, name='loan-return-entry'),
    # path('new-loan-entry/<int:id>', newLoanEntry, name='new-loan-entry'),
    path('saving-entry/<int:id>', savingsEntry, name='saving-entry'),
    path('withdraw-entry/<int:id>', withdrawEntry, name='withdraw-entry'), 
    path('new-loan-entry/<int:id>', newLoanEntry, name='new_loan_entry'),
    path('remove-loan-return-details/<int:id>', removeLoanReturnDetails, name='remove_loan_return_details'),
    path('remove-saving-withdraw-details/<int:id>', removeSavingWithdrawDetails, name='remove_saving_withdraw_details'),
    path('daily-collection', dailyCollectionList, name='daily_collection'),
    path('search-daily-collection', searchDailyCollectionList, name='search_daily_collection'),
    path('recent-entry', recentEntryList, name='recent_entry'),
    path('search-recent-entry', searchRecentEntryList, name='search_recent_entry'),
    path('search-running-client', searchRunningClient, name='search_running_client'),
    path('search-dateOver-client', searchDateOverClient, name='search_dateOver_client')

    
    # path('super-admin-register/', SuperAdminRegistrationView.as_view(), name='super_admin_register'),
]