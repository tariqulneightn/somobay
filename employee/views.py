from django.shortcuts import render, redirect

from django.db.models import Q
from datetime import datetime, date, time
import time, json
from django.contrib.auth.decorators import login_required

from employee.models import Employees
from account.models import User, UserType
from employee.forms import EmployeeRegForm, EmployeeDetailsForm
from client.forms import *
from client.models import *
from account.decorator import *


# Create your views here.
@login_required
@employee_only
def employeeDashboard(request):
    this_user = request.user
    employee = Employees.objects.get(user= this_user)
    
    all_clients = Clients.objects.filter(employee_for = employee).order_by('-created_at')

    clients_details = []
    for client in all_clients:
        if client.loan_giving_date == None:
            loan_exp_date = None
            
        else:
            loan_exp_date = client.loan_giving_date
            loan_exp_date += datetime.timedelta(days=121)
        try:
            savings_details = SavingDetails.objects.filter(client_id = client.id).order_by('created_at')
            total_savings = savings_details[len(savings_details)-1].total_savings
            saving_start_date = savings_details[0].saving_date
            print(total_savings)
        except:
            savings_details = None
            total_savings = None
            saving_start_date = None

        clients_details.append({
                'client': client,
                'loan_exp_date': loan_exp_date,
                'total_savings': total_savings,
                'saving_start_date': saving_start_date
            })


    
    context = {'all_clients': clients_details,
                }
   

    
    return render(request, 'employee/all_client.html', context)

@login_required
@employee_only
def searchClient(request):
    this_user = request.user
    employee = Employees.objects.get(user= this_user)
    this_emp_id = employee.id

    # all_employee = Employees.objects.all()
    client_name = request.GET.get('client_name')
    client_phone = request.GET.get('client_phone')
    client_nid = request.GET.get('client_nid')
    time_period = request.GET.get('return_time_period')
    if request.GET.get('return_time_period') == '':
        # time_query = Q(loan_return_period__icontains=time_period)
        all_clients = Clients.objects.filter(Q(name__icontains=client_name),
                                            Q(phone__icontains=client_phone),
                                            Q(nid__icontains=client_nid),
                                            Q(employee_for_id = this_emp_id)
                                            ).order_by('-created_at')
    else:
        # time_query = Q(loan_return_period=int(time_period))
        all_clients = Clients.objects.filter(Q(name__icontains=client_name),
                                            Q(phone__icontains=client_phone),
                                            Q(nid__icontains=client_nid),
                                            Q(loan_return_period=int(time_period)),
                                            Q(employee_for_id = this_emp_id)
                                            ).order_by('-created_at')
    

    clients_details = []
    for client in all_clients:
        if client.loan_giving_date == None:
            loan_exp_date = None
            
        else:
            loan_exp_date = client.loan_giving_date
            loan_exp_date += datetime.timedelta(days=121)
        try:
            savings_details = SavingDetails.objects.filter(client_id = client.id).order_by('created_at')
            total_savings = savings_details[len(savings_details)-1].total_savings
            saving_start_date = savings_details[0].saving_date
            print(total_savings)
        except:
            savings_details = None
            total_savings = None
            saving_start_date = None

        clients_details.append({
                'client': client,
                'loan_exp_date': loan_exp_date,
                'total_savings': total_savings,
                'saving_start_date': saving_start_date
            })


    
    context = {'all_clients': clients_details,
                }

    return render(request, 'employee/all_client.html', context)

@login_required
@employee_only
def addClient(request):
    client_form = ClientCreateForm
    this_user = request.user
    employee = Employees.objects.get(user= this_user)
    
    if request.method == "POST":
        products = request.POST.get('product')
        quantities = request.POST.get('quantity')
        prices = request.POST.get('price')
        
        product_list = products.replace(', ', ',').replace(' ', '_').split(",")
        print(products)
        print(product_list)
        quantity_list = quantities.replace(', ', ',').replace(' ', '').split(",")
        print(quantities)
        print(quantity_list)
        price_list = prices.replace(', ', ',').replace(' ', '').split(",")
        print(prices)
        print(price_list)

        if len(product_list) == len(quantity_list) == len(price_list):
            client_form = ClientCreateForm(request.POST)
            print(client_form)
            client_form.save()

            get_last_client = Clients.objects.get(nid = client_form.cleaned_data.get('nid'), created_at = date.today())
            if get_last_client and quantities !='' and prices !='' and products !='' and products !=' ' and products !=None:

                print(len(product_list))
                for i in range(len(product_list)):
                    print(i)
                    product_model = ProductDetails()
                    product_model.product_name = product_list[i]
                    product_model.quantity = int(quantity_list[i])
                    product_model.unite_price = int(price_list[i])
                    product_model.total_price = int(quantity_list[i]) * int(price_list[i])
                    product_model.client = get_last_client
                    product_model.save()

        
        return redirect('employee:all_client')
    context = {'client_form': client_form,
                'employee': employee}

    
    return render(request, 'employee/add_client.html', context)

@login_required
@employee_only
def clientDetails(request, id):
    this_client = Clients.objects.get(id= id)
    loan_details = LoanReturnDetails.objects.filter(client = this_client)
    saving_details = SavingDetails.objects.filter(client = this_client)
    clients_products = ProductDetails.objects.filter(client=this_client)


    context = {'client': this_client,
                'products': clients_products,
                'return_details': loan_details,
                'saving_details': saving_details}

    return render(request, 'employee/client_details.html', context)



    