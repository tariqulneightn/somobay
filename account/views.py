import os
from datetime import datetime, date, time, timezone

from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, FormView, RedirectView
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.core.paginator import Paginator
from django.contrib import messages, auth
from django.db.models import Q
from django.contrib.auth.hashers import make_password

from account.models import *
from account.forms import *

# Create your views here.

def home(request):
    create_user_type()
    owner_register()
    return render(request, 'home.html', {})

def create_user_type():
    table = UserType()
    usertype_table_data = UserType.objects.all()
    if len(usertype_table_data) == 0:
        obj = UserType()
        obj.id = 1
        obj.user_type = 'owner'
        obj.created_at = date.today()
        obj.updated_at = date.today
        obj.save()
        print('obj created')

        obj = UserType()
        obj.id = 2
        obj.user_type = 'employee'
        obj.created_at = date.today()
        obj.updated_at = date.today
        obj.save()

def owner_register():
    """Create the initial owner superuser from environment variables if no users exist."""
    user_table_data = User.objects.all()
    if len(user_table_data) == 0:
        owner_email = os.environ.get('DEFAULT_OWNER_EMAIL', '').strip()
        owner_password = os.environ.get('DEFAULT_OWNER_PASSWORD', '')
        if not owner_email or not owner_password:
            return
        obj = User()
        obj.id = 1
        obj.first_name = os.environ.get('DEFAULT_OWNER_NAME', 'Owner')
        obj.password = make_password(owner_password)
        obj.last_name = ''
        obj.is_superuser = 1
        obj.is_staff = 1
        obj.is_active = 1
        obj.date_joined = date.today()
        obj.email = owner_email
        obj.phone = os.environ.get('DEFAULT_OWNER_PHONE', '')
        obj.updated_at = date.today()
        obj.user_type = UserType.objects.get(user_type='owner', id=1)
        obj.save()

class LoginView(FormView):                                           ##----------- View function for login. Extending Django FormView class
    owner_success_url= '/owner/all-client/'               ##----------- success url if logged in as user_type == admin
    employee_success_url= '/employee/all-client/'
    # doctor_success_url= '/doctor/dashboard/'
    # manager_success_url= '/manager/dashboard/'
    # general_staff_success_url= '/staff/dashboard/'

    general_success_url= '/'                                         ##----------- if user type is undefined


    form_class = LoginForm
    template_name = "account/login.html"

    extra_context = {
        'title': 'Login'
    }
    # user_role = UserType.objects.get(user_type='admin')

    def dispatch(self, request, *args, **kwargs):                     ##----------- Track and redirect as the requisting user is authenticated 
        if self.request.user.is_authenticated:
            return redirect(self.get_success_url())                   ##----------- if authenticated redirect to success url as user_type
        return super().dispatch(self.request, *args, **kwargs)        ##----------- if not authenticated redirect to login page

    def get_success_url(self):                                        ##----------- finds the correct success url as user_type
        if 'next' in self.request.GET and self.request.GET['next'] != '':
            return self.request.GET['next'] 

        else:
            if self.request.user.user_type == UserType.objects.get(user_type='owner'):                ##----------- if admid return the admin dashboard
                print(self.request.user.user_type)
                return self.owner_success_url
            if self.request.user.user_type == UserType.objects.get(user_type='employee'):                ##----------- if client return the client dashboard
                print(self.request.user.user_type)
                return self.employee_success_url
            # if self.request.user.user_type == UserType.objects.get(user_type='doctor'):                ##----------- if doctor return the doctor dashboard
            #     print(self.request.user.user_type)
            #     return self.doctor_success_url
            # if self.request.user.user_type == UserType.objects.get(user_type='manager'):                ##----------- if manger return the manager dashboard
            #     print(self.request.user.user_type)
            #     return self.manager_success_url
            # if self.request.user.user_type == UserType.objects.get(user_type='general_staff'):                ##----------- if general_staff return the general_staff dashboard
            #     print(self.request.user.user_type)
            #     return self.general_staff_success_url
            else:
                print(self.request.user.user_type)
                return self.general_success_url


    def get_form_class(self):                                         ##----------- get the form of this class
        print(self.form_class(data=self.request.POST))
        return self.form_class

    def form_valid(self, form):                                       ##----------- if submited form is valid get the user and call success_url
        print("valid Form")
        auth.login(self.request, form.get_user())

        # write_log(self.request, self.request.user, "Logged In", CHANGE)

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        print("invalid form")
        return self.render_to_response(self.get_context_data(form=form)) ##------ if submited form is invalid load the form again

    # return render(request, 'login.html', {})

class LogoutView(RedirectView):                                          ##------ Control if user is logging out

    url = '/account/login/'                                                      ##------ url after logout

    def get(self, request, *args, **kwargs):

        # write_log(self.request, self.request.user, "Logged Out", CHANGE)

        auth.logout(request)
        print('Logged out')
        print(request.user)
        messages.success(request, "You are logged out")
        return super(LogoutView, self).get(request, *args, **kwargs)



def passwordReset(request):                                              ##-------- This function is to reset passwod
    if request.method == 'POST':
        email = request.POST.get('email')
        pass1= request.POST.get('password1')
        pass2= request.POST.get('password2')
        # print(email)
        try: 
            email= User.objects.get(email=email)
            if email:                                                    ##-------- Checking if the given email is into user table (registered)
                if pass1 == pass2:                                       ##-------- confirming the new password
                    email.set_password(pass1)                            ##-------- set new password
                    email.save()                                         ##-------- save the password
            return redirect('login_page')                                ## ------- after successful reset redirect to login page
        except Exception as e:
            print(e)
            context = {'message':"You are not registered"}
            return render(request, 'reset_password.html', context)      ##--------- if given email is wrong render with message
    return render(request, 'reset_password.html', {})
