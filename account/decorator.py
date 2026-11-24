from django.http import HttpResponse
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

def owner_only(view_func):
    def wrapper_function(request, *args, **kwargs):
        user_type = request.user.user_type.user_type
        if user_type== 'owner':
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
            
    return wrapper_function

def employee_only(view_func):
    def wrapper_function(request, *args, **kwargs):
        user_type = request.user.user_type.user_type
        if user_type== 'employee':
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
            
    return wrapper_function



