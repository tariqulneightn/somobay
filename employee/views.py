from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from account.decorator import employee_only
from client.forms import ClientCreateForm
from client.models import Clients, LoanReturnDetails, ProductDetails, SavingDetails
from client.queries import build_client_search_filters, paginate_clients_with_savings
from datetime import date
from employee.models import Employees


@login_required
@employee_only
def employeeDashboard(request):
    employee = Employees.objects.get(user=request.user)
    all_clients = Clients.objects.filter(employee_for=employee).order_by('-created_at')
    context = paginate_clients_with_savings(request, all_clients)
    return render(request, 'employee/all_client.html', context)


@login_required
@employee_only
def searchClient(request):
    employee = Employees.objects.get(user=request.user)
    filters = build_client_search_filters(
        request,
        include_membership=False,
        include_employee=False,
        include_period=True,
    )
    all_clients = Clients.objects.filter(filters, employee_for_id=employee.id).order_by('-created_at')
    context = paginate_clients_with_savings(request, all_clients)
    return render(request, 'employee/all_client.html', context)


@login_required
@employee_only
def addClient(request):
    client_form = ClientCreateForm
    employee = Employees.objects.get(user=request.user)

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

            get_last_client = Clients.objects.get(nid=client_form.cleaned_data.get('nid'), created_at=date.today())
            if get_last_client and quantities != '' and prices != '' and products != '' and products != ' ' and products is not None:
                for i in range(len(product_list)):
                    product_model = ProductDetails()
                    product_model.product_name = product_list[i]
                    product_model.quantity = int(quantity_list[i])
                    product_model.unite_price = int(price_list[i])
                    product_model.total_price = int(quantity_list[i]) * int(price_list[i])
                    product_model.client = get_last_client
                    product_model.save()

        return redirect('employee:all_client')

    context = {
        'client_form': client_form,
        'employee': employee,
    }
    return render(request, 'employee/add_client.html', context)


@login_required
@employee_only
def clientDetails(request, id):
    this_client = Clients.objects.select_related('employee_for__user').get(id=id)
    loan_details = LoanReturnDetails.objects.filter(client=this_client)
    saving_details = SavingDetails.objects.filter(client=this_client)
    clients_products = ProductDetails.objects.filter(client=this_client)

    context = {
        'client': this_client,
        'products': clients_products,
        'return_details': loan_details,
        'saving_details': saving_details,
    }
    return render(request, 'employee/client_details.html', context)
