from datetime import date, datetime as dt, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render

from account.decorator import owner_only
from account.models import User, UserType
from client.forms import ClientCreateForm
from client.models import Clients, LoanReturnDetails, ProductDetails, SavingDetails
from client.queries import (
    DAY_LIMIT_OFFSETS,
    LOAN_PERIOD_DAYS,
    build_client_search_filters,
    build_daily_collection_context,
    calculate_employee_percentages,
    get_earliest_collection_dates,
    paginate_clients_with_savings,
    paginate_loan_clients,
    paginate_recent_entries,
)
from employee.forms import EmployeeDetailsForm, EmployeeRegForm
from employee.models import Employees


def eachPageObject(request, obj_list, obj_per_page, per_page_link):
    paginator = Paginator(obj_list, obj_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'pagination_data_list': page_obj,
        'per_page_objects': obj_per_page,
        'per_page_link': per_page_link,
    }
    return context


# Create your views here.
@login_required
@owner_only
def ownerDashboard(request):
    all_employee = Employees.objects.select_related('user').all()
    all_clients = Clients.objects.all().order_by('-loan_giving_date', '-register_date')
    context = paginate_clients_with_savings(request, all_clients)
    context['all_employee'] = all_employee
    return render(request, 'owner/all_client.html', context)


def runningClient(request):
    today_date = date.today()
    all_employee = Employees.objects.select_related('user').all()
    loan_given_clients = Clients.objects.filter(
        loan_giving_date__isnull=False,
        loan_giving_date__lt=today_date,
        loan_giving_date__gt=today_date - timedelta(days=LOAN_PERIOD_DAYS),
    ).order_by('-register_date')
    context = paginate_loan_clients(request, loan_given_clients, require_return_entry=False)
    context['all_employee'] = all_employee
    return render(request, 'owner/running_client.html', context)


def expiredClient(request):
    today_date = date.today()
    all_employee = Employees.objects.select_related('user').all()
    loan_given_clients = Clients.objects.filter(
        loan_giving_date__isnull=False,
        loan_giving_date__lt=today_date - timedelta(days=LOAN_PERIOD_DAYS),
    ).order_by('-register_date')
    context = paginate_loan_clients(request, loan_given_clients, require_return_entry=True)
    context['all_employee'] = all_employee
    return render(request, 'owner/expired_client.html', context)


@login_required
@owner_only
def searchClient(request):
    date_from_raw = (request.GET.get('date_from') or '').strip()
    date_to_raw = (request.GET.get('date_to') or '').strip()

    filters = build_client_search_filters(
        request,
        include_membership=True,
        include_employee=True,
        include_period=True,
    )
    if date_from_raw or date_to_raw:
        date_from = dt.strptime(date_from_raw, "%Y-%m-%d").date() if date_from_raw else date(2018, 1, 1)
        date_to = dt.strptime(date_to_raw, "%Y-%m-%d").date() if date_to_raw else date.today()
        filters &= Q(loan_giving_date__range=[date_from, date_to])

    all_employee = Employees.objects.select_related('user').all()
    all_clients = Clients.objects.filter(filters).order_by('-loan_giving_date', '-register_date')
    context = paginate_clients_with_savings(request, all_clients)
    context['all_employee'] = all_employee
    return render(request, 'owner/all_client.html', context)


@login_required
@owner_only
def addClient(request):
    client_form = ClientCreateForm
    all_employee = Employees.objects.select_related('user').filter(user__is_active=True)

    if request.method == "POST":
        products = request.POST.get('product')
        quantities = request.POST.get('quantity')
        prices = request.POST.get('price')

        product_list = products.replace(', ', ',').replace(' ', '_').split(",")
        quantity_list = quantities.replace(', ', ',').replace(' ', '').split(",")
        price_list = prices.replace(', ', ',').replace(' ', '').split(",")

        if len(product_list) == len(quantity_list) == len(price_list):
            client_form = ClientCreateForm(request.POST)
            client_form.save()

            get_last_client = Clients.objects.filter(nid=client_form.cleaned_data.get('nid'), created_at=date.today())[0]
            if get_last_client and quantities != '' and prices != '' and products != '' and products != ' ' and products is not None:
                for i in range(len(product_list)):
                    product_model = ProductDetails()
                    product_model.product_name = product_list[i]
                    product_model.quantity = int(quantity_list[i])
                    product_model.unite_price = int(price_list[i])
                    product_model.total_price = int(quantity_list[i]) * int(price_list[i])
                    product_model.client = get_last_client
                    product_model.save()

        return redirect('owner:all_client')
    context = {
        'client_form': client_form,
        'all_employee': all_employee,
    }
    return render(request, 'owner/add_client.html', context)


@login_required
@owner_only
def editClient(request, id):
    all_employee = Employees.objects.select_related('user').all()
    client = Clients.objects.get(id=id)
    if request.method == 'POST':
        client.membership_no = request.POST.get('membership_no')
        client.name = request.POST.get('name')
        client.fathers_name = request.POST.get('fathers_name')
        if request.POST.get('birthdate') != '':
            client.birthdate = request.POST.get('birthdate')

        client.nid = request.POST.get('nid')
        client.phone = request.POST.get('phone')
        client.present_address = request.POST.get('present_address')
        client.business_address = request.POST.get('business_address')
        client.business_type = request.POST.get('business_type')
        if request.POST.get('loan_amount') != '':
            client.loan_amount = int(request.POST.get('loan_amount'))
        if request.POST.get('returnable_amount') != '':
            client.returnable_amount = int(request.POST.get('returnable_amount'))

        if request.POST.get('loan_giving_date') == '':
            client.loan_giving_date = None
        else:
            client.loan_giving_date = request.POST.get('loan_giving_date')

        client.employee_for_id = int(request.POST.get('employee_for'))

        if request.POST.get('taking_loan') in (None, '', 'off'):
            client.taking_loan = False
        elif request.POST.get('taking_loan') == 'on':
            client.taking_loan = True

        if request.POST.get('saving_money') in (None, '', 'off'):
            client.saving_money = False
        elif request.POST.get('saving_money') == 'on':
            client.saving_money = True

        if request.POST.get('loan_return_period') is not None:
            client.loan_return_period = int(request.POST.get('loan_return_period'))

        if request.POST.get('register_date') != '':
            client.register_date = request.POST.get('register_date')

        client.save()
        return redirect('owner:client_details', id=id)

    context = {
        'client': client,
        'all_employee': all_employee,
    }
    return render(request, 'owner/edit_client.html', context)


@login_required
@owner_only
def employeeList(request):
    all_employee = Employees.objects.select_related('user').order_by('created_at')
    all_employee_with_percentage = calculate_employee_percentages(all_employee)
    return render(request, 'owner/employee_list.html', {'all_employee': all_employee_with_percentage})


@login_required
@owner_only
def addEmployee(request):
    user_form = EmployeeRegForm
    emp_detail_form = EmployeeDetailsForm
    if request.method == 'POST':
        user_form = EmployeeRegForm(request.POST)
        emp_detail_form = EmployeeDetailsForm(request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            password = user_form.cleaned_data.get('password')
            user.set_password(password)
            user.is_staff = False
            user.is_superuser = False
            user.is_active = True
            user.user_type = UserType.objects.get(user_type='employee')
            user.save()
            try:
                current_user = User.objects.get(email=user_form.cleaned_data.get('email'))
            except Exception:
                current_user = False
            if current_user is not False and emp_detail_form.is_valid():
                detail = emp_detail_form.save(commit=False)
                detail.user_id = current_user.id
                detail.save()
                return redirect('owner:all_employee')
    context = {
        'user_form': user_form,
        'emp_detail_form': emp_detail_form,
    }
    return render(request, 'owner/add_employee.html', context)


def editEmployee(request, id):
    employee = Employees.objects.select_related('user').get(id=id)
    user = employee.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.email = request.POST.get('email')
        employee.fathers_name = request.POST.get('fathers_name')
        employee.nid = request.POST.get('nid')
        user.phone = request.POST.get('phone')
        employee.present_address = request.POST.get('present_address')
        employee.permanent_address = request.POST.get('permanent_address')
        employee.designation = request.POST.get('designation')

        if request.POST.get('birthdate') != '':
            employee.birthdate = request.POST.get('birthdate')

        if request.POST.get('password') != '':
            user.password = make_password(request.POST.get('password'))

        user.save()
        employee.save()
        return redirect('owner:all_employee')

    context = {'employee': employee}
    return render(request, 'owner/edit_employee.html', context)


@login_required
@owner_only
def clientDetails(request, id):
    this_client = Clients.objects.select_related('employee_for__user').get(id=id)
    loan_details = LoanReturnDetails.objects.filter(client=this_client).order_by("loan_return_date")
    saving_details = SavingDetails.objects.filter(client=this_client).order_by("saving_date", "withdraw_date")
    clients_products = ProductDetails.objects.filter(client=this_client).order_by("created_at")

    remaining_amount = bool(this_client.loan_amount)
    if len(loan_details) > 0 and loan_details[len(loan_details) - 1].remaining_loan == 0:
        remaining_amount = False

    context = {
        'client': this_client,
        'products': clients_products,
        'return_details': loan_details,
        'saving_details': saving_details,
        'remaining_amount': remaining_amount,
    }
    return render(request, 'owner/client_details.html', context)


def loanReturnEntry(request, id):
    if request.method == "POST":
        get_previous_return = LoanReturnDetails.objects.filter(client=id)
        client_obj = Clients.objects.get(id=id)

        obj = LoanReturnDetails()
        obj.client = client_obj
        obj.loan_return_amount = int(request.POST.get("loan_return_amount"))
        obj.loan_return_date = request.POST.get("loan_return_date")
        obj.employee_id = client_obj.employee_for_id

        total_return = sum(prev_return.loan_return_amount for prev_return in get_previous_return)
        total_return += obj.loan_return_amount

        remaining_loan_amount = client_obj.returnable_amount - total_return
        obj.total_returned = total_return
        obj.remaining_loan = remaining_loan_amount
        obj.save()

        if request.user.user_type.user_type == 'owner':
            return redirect('owner:client_details', id=id)
        if request.user.user_type.user_type == 'employee':
            return redirect('employee:client_details', id=id)


def savingsEntry(request, id):
    if request.method == "POST":
        get_previous_saving = SavingDetails.objects.filter(client=id)
        client_obj = Clients.objects.get(id=id)

        obj = SavingDetails()
        obj.client = client_obj
        obj.saving_amount = int(request.POST.get("saving_amount"))
        obj.saving_date = request.POST.get("saving_date")
        obj.employee_id = client_obj.employee_for_id

        total_saving = sum(prev.saving_amount for prev in get_previous_saving) + obj.saving_amount
        total_withdraw = sum(prev.withdraw_amount for prev in get_previous_saving)

        obj.total_savings = total_saving
        obj.total_withdraw = total_withdraw
        obj.remaining_saving = total_saving - total_withdraw
        obj.save()

        if request.user.user_type.user_type == 'owner':
            return redirect('owner:client_details', id=id)
        if request.user.user_type.user_type == 'employee':
            return redirect('employee:client_details', id=id)


def withdrawEntry(request, id):
    if request.method == "POST":
        get_previous_saving = SavingDetails.objects.filter(client=id)
        client_obj = Clients.objects.get(id=id)

        obj = SavingDetails()
        obj.client = client_obj
        obj.withdraw_amount = int(request.POST.get("withdraw_amount"))
        obj.withdraw_date = request.POST.get("withdraw_date")
        obj.employee_id = client_obj.employee_for_id

        total_saving = sum(prev.saving_amount for prev in get_previous_saving)
        total_withdraw = sum(prev.withdraw_amount for prev in get_previous_saving) + obj.withdraw_amount

        obj.total_savings = total_saving
        obj.total_withdraw = total_withdraw
        obj.remaining_saving = total_saving - total_withdraw
        obj.save()

        if request.user.user_type.user_type == 'owner':
            return redirect('owner:client_details', id=id)
        if request.user.user_type.user_type == 'employee':
            return redirect('employee:client_details', id=id)


def newLoanEntry(request, id):
    if request.method == "POST":
        obj = Clients.objects.get(id=id)
        new_loan_amount = int(request.POST.get("new_loan_amount"))

        obj.loan_amount = new_loan_amount
        obj.loan_giving_date = request.POST.get("new_loan_date")
        obj.loan_return_period = int(request.POST.get("loan_return_period"))
        obj.returnable_amount = int(request.POST.get("returnable_amount"))
        obj.taking_loan = True
        obj.save()

        LoanReturnDetails.objects.filter(client=obj).delete()

        if request.user.user_type.user_type == 'owner':
            return redirect('owner:client_details', id=id)
        if request.user.user_type.user_type == 'employee':
            return redirect('employee:client_details', id=id)


@login_required
@owner_only
def removeClient(request, id):
    client = Clients.objects.get(id=id)
    client.delete()
    return redirect('owner:all_client')


@login_required
@owner_only
def removeEmployee(request, id):
    employee = Employees.objects.get(id=id)
    user = User.objects.get(id=employee.user_id)
    user.is_active = False
    user.save()
    return redirect('owner:all_employee')


@login_required
@owner_only
def activateEmployee(request, id):
    employee = Employees.objects.get(id=id)
    user = User.objects.get(id=employee.user_id)
    user.is_active = True
    user.save()
    return redirect('owner:all_employee')


@login_required
@owner_only
def removeLoanReturnDetails(request, id):
    this_data = LoanReturnDetails.objects.get(id=id)
    this_data.delete()
    return redirect('owner:client_details', id=this_data.client_id)


@login_required
@owner_only
def removeSavingWithdrawDetails(request, id):
    this_data = SavingDetails.objects.get(id=id)
    this_data.delete()
    return redirect('owner:client_details', id=this_data.client_id)


def percentageCalculate(all_employee):
    return calculate_employee_percentages(all_employee)


def dailyCollectionList(request):
    all_employee = Employees.objects.select_related('user').all()
    today_date = date.today()
    first_loan_date, first_saving_date = get_earliest_collection_dates()
    candidate_dates = [d for d in (first_loan_date, first_saving_date) if d is not None]
    earliest_date = min(candidate_dates) if candidate_dates else today_date
    context = build_daily_collection_context(request, all_employee, earliest_date, today_date)
    return render(request, 'owner/daily_collection.html', context)


def searchDailyCollectionList(request):
    all_employee = Employees.objects.select_related('user').all()
    today_date = date.today()
    first_loan_date, first_saving_date = get_earliest_collection_dates()
    candidate_dates = [d for d in (first_loan_date, first_saving_date) if d is not None]
    first_date = min(candidate_dates) if candidate_dates else today_date

    date_from_raw = (request.GET.get('date_from') or '').strip()
    date_to_raw = (request.GET.get('date_to') or '').strip()
    employee_raw = (request.GET.get('employee') or '').strip()

    if not date_from_raw:
        date_from = first_date
    else:
        parsed_from = dt.strptime(date_from_raw, "%Y-%m-%d").date()
        date_from = first_date if parsed_from < first_date else parsed_from

    date_to = today_date if not date_to_raw else dt.strptime(date_to_raw, "%Y-%m-%d").date()
    selected_employee = Employees.objects.select_related('user').get(id=int(employee_raw)) if employee_raw else None

    context = build_daily_collection_context(
        request,
        all_employee,
        date_from,
        date_to,
        selected_employee=selected_employee,
    )
    return render(request, 'owner/daily_collection.html', context)


def recentEntryList(request):
    all_employee = Employees.objects.select_related('user').all()
    today_date = date.today()
    date_last_limit = today_date - timedelta(days=7)

    all_loan_entry = LoanReturnDetails.objects.filter(
        created_at__gt=date_last_limit,
        created_at__lte=today_date,
    ).order_by('-created_at', 'employee_id')
    all_savings_entry = SavingDetails.objects.filter(
        created_at__gt=date_last_limit,
        created_at__lte=today_date,
    ).order_by('-created_at', 'employee_id')

    context = paginate_recent_entries(request, all_employee, all_loan_entry, all_savings_entry)
    return render(request, 'owner/recent_entry.html', context)


def searchRecentEntryList(request):
    today_date = date.today()
    default_limit = today_date - timedelta(days=7)
    all_employee = Employees.objects.select_related('user').all()

    date_from_raw = (request.GET.get('date_from') or '').strip()
    date_to_raw = (request.GET.get('date_to') or '').strip()
    employee_raw = (request.GET.get('employee') or '').strip()

    if not date_from_raw:
        date_from = default_limit
    else:
        parsed_from = dt.strptime(date_from_raw, "%Y-%m-%d").date()
        date_from = default_limit if parsed_from < default_limit else parsed_from

    if not date_to_raw:
        date_to = today_date
    else:
        parsed_to = dt.strptime(date_to_raw, "%Y-%m-%d").date()
        date_to = today_date if parsed_to > today_date else parsed_to

    loan_qs = LoanReturnDetails.objects.filter(
        loan_return_date__isnull=False,
        loan_return_date__range=[date_from, date_to],
    )
    saving_qs = SavingDetails.objects.filter(
        saving_date__isnull=False,
        saving_date__range=[date_from, date_to],
    )
    if employee_raw:
        emp_id = int(employee_raw)
        loan_qs = loan_qs.filter(employee_id=emp_id)
        saving_qs = saving_qs.filter(employee_id=emp_id)

    loan_qs = loan_qs.order_by('-created_at', 'employee_id')
    saving_qs = saving_qs.order_by('-created_at', 'employee_id')
    context = paginate_recent_entries(request, all_employee, loan_qs, saving_qs)
    return render(request, 'owner/recent_entry.html', context)


@login_required
@owner_only
def searchRunningClient(request):
    today_date = date.today()
    all_employee = Employees.objects.select_related('user').all()
    day_limit = int(request.GET.get('day_limit') or 0)
    max_days_ago, min_days_ago = DAY_LIMIT_OFFSETS.get(day_limit, (LOAN_PERIOD_DAYS, 0))

    filters = build_client_search_filters(request, include_membership=True, include_employee=True)
    filters &= Q(
        loan_giving_date__isnull=False,
        loan_giving_date__gt=today_date - timedelta(days=max_days_ago),
        loan_giving_date__lte=today_date - timedelta(days=min_days_ago),
    )
    loan_given_clients = Clients.objects.filter(filters).order_by('-register_date')
    context = paginate_loan_clients(request, loan_given_clients, require_return_entry=False)
    context['all_employee'] = all_employee
    return render(request, 'owner/running_client.html', context)


@login_required
@owner_only
def searchDateOverClient(request):
    today_date = date.today()
    all_employee = Employees.objects.select_related('user').all()
    filters = build_client_search_filters(request, include_membership=True, include_employee=True)
    filters &= Q(
        loan_giving_date__isnull=False,
        loan_giving_date__lt=today_date - timedelta(days=LOAN_PERIOD_DAYS),
    )
    loan_given_clients = Clients.objects.filter(filters).order_by('-register_date')
    context = paginate_loan_clients(request, loan_given_clients, require_return_entry=True)
    context['all_employee'] = all_employee
    return render(request, 'owner/expired_client.html', context)
