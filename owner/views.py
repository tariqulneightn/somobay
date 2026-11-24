from re import U
from django.shortcuts import render, redirect

from django.db.models import Q
from datetime import datetime, date, time, timedelta
from datetime import datetime
import time, json
from django.contrib.auth.decorators import login_required
from django.urls import conf
from django.contrib.auth.hashers import make_password

from employee.models import Employees
from account.models import User, UserType
from employee.forms import EmployeeRegForm, EmployeeDetailsForm
from client.forms import *
from client.models import *
from account.decorator import *
from django.core.paginator import Paginator


def eachPageObject(request, obj_list, obj_per_page, per_page_link):
    paginator = Paginator(obj_list, obj_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'pagination_data_list': page_obj, 
        'per_page_objects': obj_per_page, 
        'per_page_link': per_page_link
    }

    return context



# Create your views here.
@login_required
@owner_only
def ownerDashboard(request):
    all_employee = Employees.objects.all()
    all_clients = Clients.objects.all().order_by('-loan_giving_date', '-register_date')
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

    obj_per_page = 50
    per_page_link = 5
    
    context = eachPageObject(request, clients_details, obj_per_page, per_page_link)
    # context = {'all_clients': clients_details,
    #             'all_employee': all_employee}
    
    context['all_employee'] = all_employee

    return render(request, 'owner/all_client.html', context)

def runningClient(request):
    all_employee = Employees.objects.all()
    loan_given_clients = Clients.objects.filter(Q(loan_giving_date__isnull=False)).order_by('-register_date')
    # print(loan_given_clients)
    all_clients = []
    clients_details = []
    for client in loan_given_clients:
        loan_taking_date = client.loan_giving_date
        lowest_date_range = loan_taking_date
        highest_date_range = lowest_date_range + datetime.timedelta(days=121)
        try:
            last_return_queryset = LoanReturnDetails.objects.filter(client_id=client.id).latest('loan_return_date')
            remaining_loan = last_return_queryset.remaining_loan
            # print(remaining_loan)
        except:
            remaining_loan = client.loan_amount
        if loan_taking_date < date.today() < highest_date_range and remaining_loan != 0:
            print(client)
            print(remaining_loan)
            clients_details.append({'client':client,
                                'remaining_loan': remaining_loan,
                                'loan_exp_date': highest_date_range,})

    context = {'all_clients': clients_details,
                'all_employee': all_employee}

    return render(request, 'owner/running_client.html', context)

def expiredClient(request):
    all_employee = Employees.objects.all()
    loan_given_clients = Clients.objects.filter(Q(loan_giving_date__isnull=False)).order_by('-register_date')
    print(loan_given_clients)
    all_clients = []
    clients_details = []
    for client in loan_given_clients:
        loan_taking_date = client.loan_giving_date
        lowest_date_range = loan_taking_date
        highest_date_range = lowest_date_range + datetime.timedelta(days=121)
        try:
            last_return = LoanReturnDetails.objects.filter(client_id=client.id).latest('loan_return_date')
            if date.today() > highest_date_range and last_return.remaining_loan != 0:
                clients_details.append({'client':client,
                                    'remaining_loan': last_return.remaining_loan,
                                    'loan_exp_date': highest_date_range,})
        except:
            pass
        

    
    context = {'all_clients': clients_details,
                'all_employee': all_employee}

    return render(request, 'owner/expired_client.html', context)

@login_required
@owner_only
def searchClient(request):
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    today_date = date.today()
    first_date = '2018-01-01'

    if date_from == '':
        date_from = dt.strptime(first_date, "%Y-%m-%d").date()
    else:
        date_from = dt.strptime(request.GET.get('date_from'), "%Y-%m-%d").date()

    if date_to == '':
        date_to = today_date
    else:
        date_to = dt.strptime(request.GET.get('date_to'), "%Y-%m-%d").date()

    all_employee = Employees.objects.all()
    mem_id = request.GET.get('mem_id')
    client_name = request.GET.get('client_name')
    client_phone = request.GET.get('client_phone')
    client_nid = request.GET.get('client_nid')
    time_period = request.GET.get('return_time_period')
    employee = request.GET.get('employee')
    if request.GET.get('employee') == '':
        emp_query = Q()
    else:
        emp_query = Q(employee_for_id=employee)
    if request.GET.get('return_time_period') == '':
        # time_query = Q(loan_return_period__icontains=time_period)
        all_clients = Clients.objects.filter(Q(name__icontains=client_name),
                                            Q(phone__icontains=client_phone),
                                            Q(membership_no__icontains=mem_id),
                                            Q(nid__icontains=client_nid),
                                            emp_query,
                                            Q(loan_giving_date__range=[date_from,          date_to])
                                            ).order_by('-loan_giving_date', '-register_date')
    else:
        # time_query = Q(loan_return_period=int(time_period))
        all_clients = Clients.objects.filter(Q(name__icontains=client_name),
                                            Q(phone__icontains=client_phone),
                                            Q(membership_no__icontains=mem_id),
                                            Q(nid__icontains=client_nid),
                                            Q(loan_return_period=int(time_period)),
                                            emp_query,
                                            Q(loan_giving_date__range=[date_from,          date_to])
                                            ).order_by('-loan_giving_date', '-register_date')


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

    obj_per_page = 50
    per_page_link = 5

    context = eachPageObject(request, clients_details, obj_per_page, per_page_link)
    
    # context = {'all_clients': clients_details,
    #             'all_employee': all_employee}
    
    url_part = request.get_full_path().split('/?')[1]
    url_part = url_part.rsplit('&page')[0]
    print(url_part)
    
    context['all_employee'] = all_employee
    context['search_parameter'] = url_part

    return render(request, 'owner/all_client.html', context)

@login_required
@owner_only
def addClient(request):
    client_form = ClientCreateForm
    all_employee = Employees.objects.filter(user__is_active = True)
    
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
            # print(client_form)
            client_form.save()

            get_last_client = Clients.objects.filter(nid = client_form.cleaned_data.get('nid'), created_at = date.today())[0]
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

        
        return redirect('owner:all_client')
    context = {'client_form': client_form,
                'all_employee':all_employee}

    return render(request, 'owner/add_client.html', context)

@login_required
@owner_only
def editClient(request, id):
    all_employee = Employees.objects.all()
    client = Clients.objects.get(id = id)
    if request.method == 'POST':
        client.membership_no = request.POST.get('membership_no')
        client.name = request.POST.get('name')
        client.fathers_name = request.POST.get('fathers_name')
        if request.POST.get('birthdate') == '':
            client.birthdate = client.birthdate
        else:
            client.birthdate = request.POST.get('birthdate')
        
        client.nid = request.POST.get('nid')
        client.phone = request.POST.get('phone')
        client.present_address = request.POST.get('present_address')
        client.business_address = request.POST.get('business_address')
        client.business_type = request.POST.get('business_type')
        if request.POST.get('loan_amount') == '':
            pass
        else:
            client.loan_amount = int(request.POST.get('loan_amount'))
        if request.POST.get('returnable_amount') == '':
            pass
        else:
            client.returnable_amount = int(request.POST.get('returnable_amount'))
        
        if request.POST.get('loan_giving_date') == '':
            client.loan_giving_date = None
        else:
            client.loan_giving_date = request.POST.get('loan_giving_date')

        client.employee_for_id = int(request.POST.get('employee_for'))

        if request.POST.get('taking_loan') == None or request.POST.get('taking_loan') == '' or request.POST.get('taking_loan') == 'off':
            client.taking_loan = False
        
        elif request.POST.get('taking_loan') == 'on':
            client.taking_loan = True
            

        if request.POST.get('saving_money') == None or request.POST.get('saving_money') == '' or request.POST.get('saving_money') == 'off':
            client.saving_money = False
        
        elif request.POST.get('saving_money') == 'on':
            client.saving_money = True
            
                

        if request.POST.get('loan_return_period') == None:
            pass
        else:
            client.loan_return_period = int(request.POST.get('loan_return_period'))

        if request.POST.get('register_date') == '':
            client.register_date = client.register_date
        else:
            client.register_date = request.POST.get('register_date')

        client.save()
        return redirect('owner:client_details', id=id)

    context = {'client': client,
                'all_employee': all_employee}
    return render(request, 'owner/edit_client.html', context)

@login_required
@owner_only
def employeeList(request):
    all_employee = Employees.objects.all().order_by('created_at')
    
    all_employee_with_percentage = percentageCalculate(all_employee)
    return render(request, 'owner/employee_list.html', {'all_employee':all_employee_with_percentage})

@login_required
@owner_only
def addEmployee(request):
    user_form = EmployeeRegForm
    emp_detail_form = EmployeeDetailsForm
    if request.method == 'POST':
        user_form = EmployeeRegForm(request.POST)
        emp_detail_form = EmployeeDetailsForm(request.POST)
        if user_form.is_valid():
            print('user form is valid')
            user = user_form.save(commit=False)
            password = user_form.cleaned_data.get('password')
            user.set_password(password)
            user.is_staff = False
            user.is_superuser = False
            user.is_active = True
            user.user_type = UserType.objects.get(user_type='employee')         ## defining user_type as doctor for user table
            print("user_form saved")
            user.save()
            try:
                current_user = User.objects.get(email=user_form.cleaned_data.get('email')) ## checking if the user(doctor) is created into user table
                print(current_user)
            except:
                print('none')
                current_user = False
            if current_user != False:                                       ## if the doctor is created try to store doctor's details
                print(emp_detail_form)
                if emp_detail_form.is_valid():
                    detail = emp_detail_form.save(commit=False)
                    # detail.name = user_form.cleaned_data.get('first_name')
                    detail.user_id = current_user.id
                    print('emp_detail_form saved')
                    detail.save()
                    return redirect('owner:all_employee')
    context = {'user_form':user_form,
                'emp_detail_form':emp_detail_form}

    return render(request, 'owner/add_employee.html', context)

def editEmployee(request, id):
    employee = Employees.objects.get(id = id)
    user = User.objects.get(id = employee.user.id)
    print(user)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.email = request.POST.get('email')
        # password = request.POST.get('password')
        employee.fathers_name = request.POST.get('fathers_name')
        # birthdate = request.POST.get('birthdate')
        employee.nid = request.POST.get('nid')
        user.phone = request.POST.get('phone')
        employee.present_address = request.POST.get('present_address')
        employee.permanent_address = request.POST.get('permanent_address')
        employee.designation = request.POST.get('designation')

        if request.POST.get('birthdate') == '':
            employee.birthdate = employee.birthdate
        else:
            employee.birthdate = request.POST.get('birthdate')

        if request.POST.get('password') == '':
            pass
        else:
            user.password = make_password(request.POST.get('password'))

        user.save()
        employee.save()
        return redirect('owner:all_employee')

    context = {'employee': employee}
    return render(request, 'owner/edit_employee.html', context)

@login_required
@owner_only
def clientDetails(request, id):
    this_client = Clients.objects.get(id= id)
    loan_details = LoanReturnDetails.objects.filter(client = this_client).order_by("loan_return_date")
    saving_details = SavingDetails.objects.filter(client = this_client).order_by("saving_date", "withdraw_date")
    clients_products = ProductDetails.objects.filter(client=this_client).order_by("created_at")

    if this_client.loan_amount:
        remaining_amount = True
    else:
        remaining_amount = False
    if len(loan_details)>0:
        if loan_details[len(loan_details)-1].remaining_loan == 0:
            remaining_amount = False    
        # else:
        #     remaining_amount = False
    
    print(remaining_amount)
    context = {'client': this_client,
                'products': clients_products,
                'return_details': loan_details,
                'saving_details': saving_details,
                'remaining_amount': remaining_amount}

    return render(request, 'owner/client_details.html', context)

def loanReturnEntry(request, id):
    
    if request.method == "POST":
        get_previous_return = LoanReturnDetails.objects.filter(client= id)
        

        print(id)
        print(int(request.POST.get("loan_return_amount")))
        obj = LoanReturnDetails()
        obj.client = Clients.objects.get(id=id)
        obj.loan_return_amount = int(request.POST.get("loan_return_amount"))
        obj.loan_return_date = request.POST.get("loan_return_date")
        obj.employee_id = Clients.objects.get(id=id).employee_for_id

        total_return = 0
        for prev_return in get_previous_return:
            total_return = total_return + prev_return.loan_return_amount
        total_return = total_return + int(request.POST.get("loan_return_amount"))

        remaining_loan_amount = Clients.objects.get(id = id).returnable_amount - total_return
        print(remaining_loan_amount)

        obj.total_returned = total_return
        obj.remaining_loan = remaining_loan_amount
        obj.save()
        if request.user.user_type.user_type == 'owner':
            return redirect('owner:client_details', id=id)
        elif request.user.user_type.user_type == 'employee':
            return redirect('employee:client_details', id=id)

def savingsEntry(request, id):
    
    if request.method == "POST":
        get_previous_saving = SavingDetails.objects.filter(client= id)
        
        print(id)
        print(int(request.POST.get("saving_amount")))
        obj = SavingDetails()
        obj.client = Clients.objects.get(id=id)
        obj.saving_amount = int(request.POST.get("saving_amount"))
        obj.saving_date = request.POST.get("saving_date")
        obj.employee_id = Clients.objects.get(id=id).employee_for_id

        total_saving = 0
        total_withdraw = 0
        for prev_saving in get_previous_saving:
            total_saving = total_saving + prev_saving.saving_amount
            total_withdraw = total_withdraw + prev_saving.withdraw_amount

        total_saving = total_saving + int(request.POST.get("saving_amount"))
        print(int(request.POST.get("saving_amount")))
        print(total_saving)

        obj.total_savings = total_saving
        obj.total_withdraw = total_withdraw
        obj.remaining_saving = total_saving - total_withdraw
        
        obj.save()
        if request.user.user_type.user_type == 'owner':
            return redirect('owner:client_details', id=id)
        elif request.user.user_type.user_type == 'employee':
            return redirect('employee:client_details', id=id)

def withdrawEntry(request, id):
    if request.method == "POST":
        get_previous_saving = SavingDetails.objects.filter(client= id)
        print(id)
        print(int(request.POST.get("withdraw_amount")))
        obj = SavingDetails()
        obj.client = Clients.objects.get(id=id)
        obj.withdraw_amount = int(request.POST.get("withdraw_amount"))
        obj.withdraw_date = request.POST.get("withdraw_date")
        obj.employee_id = Clients.objects.get(id=id).employee_for_id

        total_saving = 0
        total_withdraw = 0
        for prev_saving in get_previous_saving:
            total_saving = total_saving + prev_saving.saving_amount
            total_withdraw = total_withdraw + prev_saving.withdraw_amount

        total_withdraw = total_withdraw + int(request.POST.get("withdraw_amount"))
        print(int(request.POST.get("withdraw_amount")))
        print(total_withdraw)

        obj.total_savings = total_saving
        obj.total_withdraw = total_withdraw
        obj.remaining_saving = total_saving - total_withdraw
        obj.save()
        if request.user.user_type.user_type == 'owner':
            return redirect('owner:client_details', id=id)
        elif request.user.user_type.user_type == 'employee':
            return redirect('employee:client_details', id=id)

def newLoanEntry(request, id):
    if request.method == "POST":
        obj = Clients.objects.get(id = id)
        print(id)
        print(int(request.POST.get("new_loan_amount")))

        if obj.loan_amount == None:
            previous_loan_amount = 0
            loan_return_period = 1
        else:
            # previous_loan_amount = obj.loan_amount
            previous_loan_amount = 0
            loan_return_period = 1

        new_loan_amount = int(request.POST.get("new_loan_amount"))
        
        obj.loan_amount = new_loan_amount + previous_loan_amount
        obj.loan_giving_date = request.POST.get("new_loan_date")
        obj.loan_return_period = int(request.POST.get("loan_return_period"))
        obj.returnable_amount = int(request.POST.get("returnable_amount"))
        obj.taking_loan = True
        obj.save()

        get_related_return_details = LoanReturnDetails.objects.filter(client = obj)
        for return_details in get_related_return_details:
            return_details.delete()

        if request.user.user_type.user_type == 'owner':
            return redirect('owner:client_details', id=id)
        elif request.user.user_type.user_type == 'employee':
            return redirect('employee:client_details', id=id)
        

@login_required
@owner_only
def removeClient(request, id):
    client = Clients.objects.get(id = id)
    client.delete()
    return redirect('owner:all_client')


@login_required
@owner_only
def removeEmployee(request, id):
    employee = Employees.objects.get(id = id)
    user = User.objects.get(id = employee.user_id)

    user.is_active = False
    user.save()
    return redirect('owner:all_employee')

@login_required
@owner_only
def activateEmployee(request, id):
    employee = Employees.objects.get(id = id)
    user = User.objects.get(id = employee.user_id)

    user.is_active = True
    user.save()
    return redirect('owner:all_employee')

@login_required
@owner_only
def removeLoanReturnDetails(request, id):
    this_data = LoanReturnDetails.objects.get(id = id)
    this_data.delete()
    return redirect('owner:client_details', id=this_data.client_id)

@login_required
@owner_only
def removeSavingWithdrawDetails(request, id):
    this_data = SavingDetails.objects.get(id = id)
    this_data.delete()
    return redirect('owner:client_details', id=this_data.client_id)


def percentageCalculate(all_employee):
    todays_date = date.today()
    # lowest_date_range = todays_date - datetime.timedelta(days=121)
    # print(lowest_date_range)
    all_employee_with_percentage = []

    for employee in all_employee:
        
        total_percentage = 0.0
        _15_day_avg_percentage_ = 0.0
        _30_day_avg_percentage = 0.0
        for i in range(30):
            valid_client_cnt = 0
            return_collection_count = 0
            # _15_day_avg_percentage = 0.0
            # _30_day_avg_percentage = 0.0
            checking_date = todays_date - datetime.timedelta(days=i)
            # print(checking_date)
            clients_of_this_employee = Clients.objects.filter(employee_for = employee)
            print(clients_of_this_employee)
            for client in clients_of_this_employee:
                # valid_client_cnt = 0
                # return_collection_count = 0
                loan_taking_date = client.loan_giving_date
                # print(loan_taking_date)
                if loan_taking_date:
                    lowest_date_range = loan_taking_date
                    highest_date_range = lowest_date_range + datetime.timedelta(days=121)
                    if lowest_date_range <= checking_date <= highest_date_range:
                        # print('client still valid')
                        valid_client_cnt += 1
                        try:
                            return_collection = LoanReturnDetails.objects.get(loan_return_date = checking_date, client = client)
                        except:
                            return_collection = False
                        if return_collection:
                            return_collection_count +=1
                print(return_collection_count)
                print(valid_client_cnt)
            if valid_client_cnt != 0:        
                daily_percentage = (return_collection_count/valid_client_cnt)*100
                total_percentage = total_percentage + daily_percentage
                # print(employee.user.first_name)
                # print(return_collection_count)
                # print(valid_client_cnt)
                # print(checking_date)
                print(daily_percentage)
                # print(total_percentage)
            else:
                break
            # print(i)
            if i<=14:
                _15_day_avg_percentage = int(total_percentage/15)
                _15_day_avg_percentage_ = _15_day_avg_percentage
                # print(_15_day_avg_percentage)

            _30_day_avg_percentage = int(total_percentage/30)
            
        # print(_15_day_avg_percentage)
        # print(_30_day_avg_percentage)
        print(employee)
        all_employee_with_percentage.append({
            'employee': employee,
            '15_day_avg_percentage': _15_day_avg_percentage_,
            '30_day_avg_percentage': _30_day_avg_percentage
        })
    # print(all_employee_with_percentage)
    return all_employee_with_percentage


from django.db.models import Sum
def dailyCollectionList(request):
    all_employee = Employees.objects.all()
    today_date = date.today()
    
    loan_return_details = LoanReturnDetails.objects.all()
    first_loan_collection_date = loan_return_details.first().loan_return_date
    saving_details = SavingDetails.objects.all()
    first_saving_collection_date = saving_details.first().saving_date
    # print(first_saving_collection_date)
    context = { 'all_employee': all_employee}

    loan_date_range = int((today_date - first_loan_collection_date).days) + 1
    

    saving_date_range = int((today_date - first_saving_collection_date).days) + 1

    print(saving_date_range)

    loan_collection_details = []
    saving_collection_details = []

    for i in range(loan_date_range):
        this_date = str(today_date - datetime.timedelta(days=i))
        print(this_date)
        # this_days_return = 
        for emp in all_employee:
            total_loan_collection_by_this_emp_in_this_date = LoanReturnDetails.objects.filter(loan_return_date = this_date, client__employee_for = emp).aggregate(Sum('loan_return_amount'))
            print(total_loan_collection_by_this_emp_in_this_date)
            loan_collection_details.append({
                'date': this_date,
                'employee': emp,
                'total_collecton': total_loan_collection_by_this_emp_in_this_date
            })

    for i in range(saving_date_range):
        this_date = str(today_date - datetime.timedelta(days=i))
        print(this_date)
        # this_days_return = 
        for emp in all_employee:
            total_saving_collection_by_this_emp_in_this_date = SavingDetails.objects.filter(saving_date = this_date, client__employee_for = emp).aggregate(Sum('saving_amount'))
            print(total_saving_collection_by_this_emp_in_this_date)
            saving_collection_details.append({
                'date': this_date,
                'employee': emp,
                'total_collecton': total_saving_collection_by_this_emp_in_this_date
            })

    context = {
        'loan_details': loan_collection_details,
        'saving_details': saving_collection_details,
        'all_employee': all_employee
    }
    
    # obj_per_page = 100
    # per_page_link = 5

    # context = eachPageObject(request, loan_collection_details, obj_per_page, per_page_link)
    
    # context['all_employee'] = all_employee
    
    

    return render(request, 'owner/daily_collection.html', context)
from datetime import datetime as dt


def searchDailyCollectionList(request):
    all_employee = Employees.objects.all()

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    employee = request.GET.get('employee')
    
    # else:
    #     emp_query = Q(employee_for_id=employee)

    # print(date_from)
    # print(type(date_to))
    today_date = date.today()
    # print(today_date)
    loan_return_details = LoanReturnDetails.objects.all()
    first_loan_collection_date = loan_return_details.first().loan_return_date
    saving_details = SavingDetails.objects.all()
    first_saving_collection_date = saving_details.first().saving_date
    # print(first_saving_collection_date)
    context = { 'all_employee': all_employee}

    loan_date_range = int((today_date - first_loan_collection_date).days) + 1
    

    saving_date_range = int((today_date - first_saving_collection_date).days) + 1

    if first_loan_collection_date > first_saving_collection_date:
        first_date = first_loan_collection_date
    else:
        first_date = first_saving_collection_date

    # print(saving_date_range)

    loan_collection_details = []
    saving_collection_details = []

    if date_from == '' or dt.strptime(date_from, "%Y-%m-%d").date() < first_date:
        date_from = first_date
    else:
        date_from = dt.strptime(request.GET.get('date_from'), "%Y-%m-%d").date()

    if date_to == '':
        date_to = today_date
    else:
        date_to = dt.strptime(request.GET.get('date_to'), "%Y-%m-%d").date()

    print(date_from)
    print(date_to)

    date_range = int((date_to - date_from).days) + 1

    print(date_range)

    for i in range(date_range):
        this_date = str(date_to - datetime.timedelta(days=i))
        print(this_date)
        # this_days_return = 
        if request.GET.get('employee') == '':
            for emp in all_employee:
                total_loan_collection_by_this_emp_in_this_date = LoanReturnDetails.objects.filter(loan_return_date = this_date, client__employee_for = emp).aggregate(Sum('loan_return_amount'))
                print(total_loan_collection_by_this_emp_in_this_date)
                loan_collection_details.append({
                    'date': this_date,
                    'employee': emp,
                    'total_collecton': total_loan_collection_by_this_emp_in_this_date
                })

                total_saving_collection_by_this_emp_in_this_date = SavingDetails.objects.filter(saving_date = this_date, client__employee_for = emp).aggregate(Sum('saving_amount'))
                print(total_saving_collection_by_this_emp_in_this_date)
                saving_collection_details.append({
                    'date': this_date,
                    'employee': emp,
                    'total_collecton': total_saving_collection_by_this_emp_in_this_date
                })


        else:
            
            total_loan_collection_by_this_emp_in_this_date = LoanReturnDetails.objects.filter(loan_return_date = this_date, client__employee_for_id = employee).aggregate(Sum('loan_return_amount'))
            # print(total_loan_collection_by_this_emp_in_this_date)
            loan_collection_details.append({
                'date': this_date,
                'employee': Employees.objects.get(id = employee),
                'total_collecton': total_loan_collection_by_this_emp_in_this_date
            })

            total_saving_collection_by_this_emp_in_this_date = SavingDetails.objects.filter(saving_date = this_date, client__employee_for_id = employee).aggregate(Sum('saving_amount'))
            # print(total_saving_collection_by_this_emp_in_this_date)
            saving_collection_details.append({
                'date': this_date,
                'employee': Employees.objects.get(id = employee),
                'total_collecton': total_saving_collection_by_this_emp_in_this_date
            })

    context = {
        'loan_details': loan_collection_details,
        'saving_details': saving_collection_details,
        'all_employee': all_employee
    }

    return render(request, 'owner/daily_collection.html', context)
    
def recentEntryList(request):
    all_employee = Employees.objects.all()
    today_date = date.today()
    date_last_limit = today_date - datetime.timedelta(days=7)

    all_loan_entry = LoanReturnDetails.objects.all().order_by('-created_at', 'employee_id')
    all_savings_entry = SavingDetails.objects.all().order_by('-created_at','employee_id')

    weekly_loan_entry = []
    weekly_savings_entry = []

    for loan_entry in all_loan_entry:
        if date_last_limit < loan_entry.created_at <= today_date:
            weekly_loan_entry.append(loan_entry)

    for saving_entry in all_savings_entry:
        if date_last_limit < saving_entry.created_at <= today_date:
            weekly_savings_entry.append(saving_entry)
        
    context = {
        'all_loan_entry': weekly_loan_entry,
        'all_savings_entry': weekly_savings_entry,
        'all_employee': all_employee
    }


    print(date_last_limit)
    return render(request, 'owner/recent_entry.html', context)
    

def searchRecentEntryList(request):
    today_date = date.today()
    date_last_limit = today_date - datetime.timedelta(days=7)

    all_employee = Employees.objects.all()

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    employee = request.GET.get('employee')

    if date_from == '' or dt.strptime(date_from, "%Y-%m-%d").date() < date_last_limit:
        date_last_limit = today_date - datetime.timedelta(days=7)
        print(date_last_limit)
    else:
        date_last_limit = dt.strptime(date_from, "%Y-%m-%d").date()
        print(date_last_limit)

    if date_to == '' or dt.strptime(date_to, "%Y-%m-%d").date() > today_date:
        today_date = date.today()
        print(today_date)
    else:
        today_date = dt.strptime(date_to, "%Y-%m-%d").date()

    if employee == '':
        all_loan_entry = LoanReturnDetails.objects.all().order_by('-created_at', 'employee_id')
        all_savings_entry = SavingDetails.objects.all().order_by('-created_at', 'employee_id')
    else:
        employee = int(employee)
        all_loan_entry = LoanReturnDetails.objects.filter(employee_id = employee).order_by('-created_at', 'employee_id')
        all_savings_entry = SavingDetails.objects.filter(employee_id = employee).order_by('-created_at', 'employee_id')
    

    weekly_loan_entry = []
    weekly_savings_entry = []

    for loan_entry in all_loan_entry:
        if loan_entry.loan_return_date == None:
            pass
        else:
            if date_last_limit <= loan_entry.loan_return_date <= today_date:
                weekly_loan_entry.append(loan_entry)

    for saving_entry in all_savings_entry:
        if saving_entry.saving_date == None:
            pass
        else:
            if date_last_limit <= saving_entry.saving_date <= today_date:
                weekly_savings_entry.append(saving_entry)
        
    context = {
        'all_loan_entry': weekly_loan_entry,
        'all_savings_entry': weekly_savings_entry,
        'all_employee': all_employee
    }


    # print(date_last_limit)
    return render(request, 'owner/recent_entry.html', context)
    
    
@login_required
@owner_only
def searchRunningClient(request):

    all_employee = Employees.objects.all()
    mem_id = request.GET.get('mem_id')
    client_name = request.GET.get('client_name')
    client_phone = request.GET.get('client_phone')
    client_nid = request.GET.get('client_nid')
    # time_period = request.GET.get('return_time_period')
    employee = request.GET.get('employee')
    day_limit = int(request.GET.get('day_limit'))
    print(day_limit)
    if request.GET.get('employee') == '':
        emp_query = Q()
    else:
        emp_query = Q(employee_for_id=employee)
    # if request.GET.get('return_time_period') == '':
        # time_query = Q(loan_return_period__icontains=time_period)
    loan_given_clients = Clients.objects.filter(Q(name__icontains=client_name),
                                        Q(phone__icontains=client_phone),
                                        Q(membership_no__icontains=mem_id),
                                        Q(nid__icontains=client_nid),
                                        emp_query,
                                        Q(loan_giving_date__isnull=False)
                                        ).order_by('-register_date')
    # else:
    #     # time_query = Q(loan_return_period=int(time_period))
    #     all_clients = Clients.objects.filter(Q(name__icontains=client_name),
    #                                         Q(phone__icontains=client_phone),
    #                                         Q(membership_no__icontains=mem_id),
    #                                         Q(nid__icontains=client_nid),
    #                                         Q(loan_return_period=int(time_period)),
    #                                         emp_query
    #                                         ).order_by('-register_date')

    day_range_limit = 121

    if day_limit == 0:
        day_range_limit = 121

    all_clients = []
    clients_details = []
    for client in loan_given_clients:
        loan_taking_date = client.loan_giving_date
        lowest_date_range = loan_taking_date
        expired_date_range = loan_taking_date + datetime.timedelta(days=121)

        if day_limit == 0:
            lowest_date_range = loan_taking_date
            highest_date_range = lowest_date_range + datetime.timedelta(days=121)
        elif day_limit == 30:
            lowest_date_range = loan_taking_date
            highest_date_range = lowest_date_range + datetime.timedelta(days=31)
        elif day_limit == 60:
            lowest_date_range = loan_taking_date + datetime.timedelta(days=31)
            highest_date_range = lowest_date_range + datetime.timedelta(days=31)
        elif day_limit == 90:
            lowest_date_range = loan_taking_date + datetime.timedelta(days=61)
            highest_date_range = lowest_date_range + datetime.timedelta(days=31)
        elif day_limit == 120:
            lowest_date_range = loan_taking_date + datetime.timedelta(days=91)
            highest_date_range = lowest_date_range + datetime.timedelta(days=31)

        try:
            last_return_queryset = LoanReturnDetails.objects.filter(client_id=client.id).latest('loan_return_date')
            remaining_loan = last_return_queryset.remaining_loan
            # print(remaining_loan)
        except:
            remaining_loan = client.loan_amount
        if lowest_date_range <= date.today() < highest_date_range and remaining_loan != 0:
            # print(client)
            # print(remaining_loan)
            clients_details.append({'client':client,
                                'remaining_loan': remaining_loan,
                                'loan_exp_date': expired_date_range,})

    context = {'all_clients': clients_details,
                'all_employee': all_employee}

    return render(request, 'owner/running_client.html', context)
    
@login_required
@owner_only
def searchDateOverClient(request):

    all_employee = Employees.objects.all()
    mem_id = request.GET.get('mem_id')
    client_name = request.GET.get('client_name')
    client_phone = request.GET.get('client_phone')
    client_nid = request.GET.get('client_nid')
    # time_period = request.GET.get('return_time_period')
    employee = request.GET.get('employee')
    if request.GET.get('employee') == '':
        emp_query = Q()
    else:
        emp_query = Q(employee_for_id=employee)
    # if request.GET.get('return_time_period') == '':
        # time_query = Q(loan_return_period__icontains=time_period)
    loan_given_clients = Clients.objects.filter(Q(name__icontains=client_name),
                                        Q(phone__icontains=client_phone),
                                        Q(membership_no__icontains=mem_id),
                                        Q(nid__icontains=client_nid),
                                        emp_query,
                                        Q(loan_giving_date__isnull=False)
                                        ).order_by('-register_date')
    # else:
    #     # time_query = Q(loan_return_period=int(time_period))
    #     all_clients = Clients.objects.filter(Q(name__icontains=client_name),
    #                                         Q(phone__icontains=client_phone),
    #                                         Q(membership_no__icontains=mem_id),
    #                                         Q(nid__icontains=client_nid),
    #                                         Q(loan_return_period=int(time_period)),
    #                                         emp_query
    #                                         ).order_by('-register_date')


    all_clients = []
    clients_details = []
    for client in loan_given_clients:
        loan_taking_date = client.loan_giving_date
        lowest_date_range = loan_taking_date
        highest_date_range = lowest_date_range + datetime.timedelta(days=121)
        try:
            last_return = LoanReturnDetails.objects.filter(client_id=client.id).latest('loan_return_date')
            if date.today() > highest_date_range and last_return.remaining_loan != 0:
                clients_details.append({'client':client,
                                    'remaining_loan': last_return.remaining_loan,
                                    'loan_exp_date': highest_date_range,})
        except:
            pass
        

    
    context = {'all_clients': clients_details,
                'all_employee': all_employee}

    return render(request, 'owner/expired_client.html', context)

