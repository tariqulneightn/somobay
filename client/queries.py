"""Shared, batched database query and pagination helpers for client and collection views."""

from datetime import date, timedelta

from django.core.paginator import Paginator
from django.db.models import Count, F, IntegerField, Min, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce

from client.models import Clients, LoanReturnDetails, SavingDetails

DEFAULT_PAGE_SIZE = 50
DEFAULT_COLLECTION_DAYS_PER_PAGE = 15
LOAN_PERIOD_DAYS = 121

DAY_LIMIT_OFFSETS = {
    0: (121, 0),
    30: (31, 0),
    60: (62, 31),
    90: (92, 61),
    120: (122, 91),
}


def extract_search_parameter(request):
    """Return URL-encoded query parameters excluding the page parameter."""
    query_params = request.GET.copy()
    query_params.pop('page', None)
    return query_params.urlencode()


def build_client_search_filters(request, *, include_membership=True, include_employee=True, include_period=False):
    """Build safe Q filters from client search GET parameters without None crashes."""
    filters = Q()

    client_name = (request.GET.get('client_name') or '').strip()
    client_phone = (request.GET.get('client_phone') or '').strip()
    client_nid = (request.GET.get('client_nid') or '').strip()

    if client_name:
        filters &= Q(name__icontains=client_name)
    if client_phone:
        filters &= Q(phone__icontains=client_phone)
    if client_nid:
        filters &= Q(nid__icontains=client_nid)

    if include_membership:
        mem_id = (request.GET.get('mem_id') or '').strip()
        if mem_id:
            filters &= Q(membership_no__icontains=mem_id)

    if include_employee:
        employee_id = (request.GET.get('employee') or '').strip()
        if employee_id:
            filters &= Q(employee_for_id=int(employee_id))

    if include_period:
        time_period = (request.GET.get('return_time_period') or '').strip()
        if time_period:
            filters &= Q(loan_return_period=int(time_period))

    return filters


def paginate_clients_with_savings(request, clients_queryset, per_page=DEFAULT_PAGE_SIZE, per_page_link=5):
    """Paginate Clients in SQL first, then fetch SavingDetails in one batch query for the active page."""
    queryset = clients_queryset.select_related('employee_for__user')
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))

    page_clients = list(page_obj.object_list)
    client_ids = [client.id for client in page_clients]

    savings_by_client = {}
    if client_ids:
        savings_rows = (
            SavingDetails.objects
            .filter(client_id__in=client_ids)
            .order_by('client_id', 'created_at', 'id')
            .values('client_id', 'total_savings', 'saving_date')
        )
        for row in savings_rows:
            cid = row['client_id']
            entry = savings_by_client.get(cid)
            if entry is None:
                savings_by_client[cid] = {
                    'saving_start_date': row['saving_date'],
                    'total_savings': row['total_savings'],
                }
            else:
                entry['total_savings'] = row['total_savings']

    clients_details = []
    for client in page_clients:
        loan_exp_date = (
            client.loan_giving_date + timedelta(days=LOAN_PERIOD_DAYS)
            if client.loan_giving_date is not None
            else None
        )
        saving_info = savings_by_client.get(client.id)
        clients_details.append({
            'client': client,
            'loan_exp_date': loan_exp_date,
            'total_savings': saving_info['total_savings'] if saving_info else None,
            'saving_start_date': saving_info['saving_start_date'] if saving_info else None,
        })

    page_obj.object_list = clients_details
    return {
        'pagination_data_list': page_obj,
        'per_page_objects': per_page,
        'per_page_link': per_page_link,
        'search_parameter': extract_search_parameter(request),
    }


def paginate_loan_clients(
    request,
    base_queryset,
    *,
    require_return_entry=False,
    per_page=DEFAULT_PAGE_SIZE,
    per_page_link=5,
):
    """Annotate latest remaining loan via SQL Subquery and paginate in SQL."""
    latest_return_subquery = (
        LoanReturnDetails.objects
        .filter(client_id=OuterRef('pk'))
        .order_by('-loan_return_date', '-id')
        .values('remaining_loan')[:1]
    )

    queryset = base_queryset.select_related('employee_for__user')
    if require_return_entry:
        queryset = (
            queryset
            .annotate(computed_remaining_loan=Subquery(latest_return_subquery, output_field=IntegerField()))
            .filter(computed_remaining_loan__isnull=False)
            .exclude(computed_remaining_loan=0)
        )
    else:
        queryset = (
            queryset
            .annotate(
                computed_remaining_loan=Coalesce(
                    Subquery(latest_return_subquery, output_field=IntegerField()),
                    F('loan_amount'),
                )
            )
            .exclude(computed_remaining_loan=0)
        )

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))

    page_clients = list(page_obj.object_list)
    page_obj.object_list = [
        {
            'client': client,
            'remaining_loan': client.computed_remaining_loan,
            'loan_exp_date': client.loan_giving_date + timedelta(days=LOAN_PERIOD_DAYS),
        }
        for client in page_clients
    ]

    return {
        'pagination_data_list': page_obj,
        'per_page_objects': per_page,
        'per_page_link': per_page_link,
        'search_parameter': extract_search_parameter(request),
    }


def calculate_employee_percentages(employees):
    """Compute 15-day and 30-day collection percentages using two bulk queries."""
    todays_date = date.today()
    earliest_check_date = todays_date - timedelta(days=29)
    earliest_loan_date = earliest_check_date - timedelta(days=LOAN_PERIOD_DAYS)

    relevant_clients = list(
        Clients.objects
        .filter(
            loan_giving_date__isnull=False,
            loan_giving_date__gte=earliest_loan_date,
            loan_giving_date__lte=todays_date,
        )
        .values('id', 'employee_for_id', 'loan_giving_date')
    )

    clients_by_employee = {}
    client_ids = []
    for client in relevant_clients:
        clients_by_employee.setdefault(client['employee_for_id'], []).append(client)
        client_ids.append(client['id'])

    single_return_pairs = set()
    if client_ids:
        return_counts = (
            LoanReturnDetails.objects
            .filter(
                loan_return_date__gte=earliest_check_date,
                loan_return_date__lte=todays_date,
                client_id__in=client_ids,
            )
            .values('client_id', 'loan_return_date')
            .annotate(cnt=Count('id'))
        )
        # Preserve original .get() behavior where only a unique row for (client, date) counted.
        single_return_pairs = {
            (row['client_id'], row['loan_return_date'])
            for row in return_counts
            if row['cnt'] == 1
        }

    all_employee_with_percentage = []
    for employee in employees:
        emp_clients = clients_by_employee.get(employee.id, [])
        total_percentage = 0.0
        avg_15_day = 0
        avg_30_day = 0

        for i in range(30):
            checking_date = todays_date - timedelta(days=i)
            valid_client_cnt = 0
            return_collection_count = 0

            for client in emp_clients:
                loan_taking_date = client['loan_giving_date']
                highest_date_range = loan_taking_date + timedelta(days=LOAN_PERIOD_DAYS)
                if loan_taking_date <= checking_date <= highest_date_range:
                    valid_client_cnt += 1
                    if (client['id'], checking_date) in single_return_pairs:
                        return_collection_count += 1

            if valid_client_cnt == 0:
                break

            daily_percentage = (return_collection_count / valid_client_cnt) * 100
            total_percentage += daily_percentage
            if i <= 14:
                avg_15_day = int(total_percentage / 15)
            avg_30_day = int(total_percentage / 30)

        all_employee_with_percentage.append({
            'employee': employee,
            '15_day_avg_percentage': avg_15_day,
            '30_day_avg_percentage': avg_30_day,
        })

    return all_employee_with_percentage


def get_earliest_collection_dates():
    """Return earliest non-null loan_return_date and saving_date via SQL MIN aggregates."""
    first_loan_date = (
        LoanReturnDetails.objects
        .filter(loan_return_date__isnull=False)
        .aggregate(first_date=Min('loan_return_date'))['first_date']
    )
    first_saving_date = (
        SavingDetails.objects
        .filter(saving_date__isnull=False)
        .aggregate(first_date=Min('saving_date'))['first_date']
    )
    return first_loan_date, first_saving_date


def build_daily_collection_context(
    request,
    all_employee,
    date_from,
    date_to,
    *,
    selected_employee=None,
    days_per_page=DEFAULT_COLLECTION_DAYS_PER_PAGE,
):
    """Paginate by date range and compute daily employee totals via GROUP BY aggregates."""
    if date_from is None or date_to is None or date_to < date_from:
        date_offsets = range(0)
    else:
        total_days = (date_to - date_from).days + 1
        date_offsets = range(total_days)

    paginator = Paginator(date_offsets, days_per_page)
    page_obj = paginator.get_page(request.GET.get('page'))
    page_dates = [date_to - timedelta(days=offset) for offset in page_obj]

    target_employees = [selected_employee] if selected_employee is not None else list(all_employee)

    loan_totals_map = {}
    saving_totals_map = {}
    if page_dates and target_employees:
        page_min_date = page_dates[-1]
        page_max_date = page_dates[0]

        loan_qs = LoanReturnDetails.objects.filter(
            loan_return_date__range=[page_min_date, page_max_date],
        )
        saving_qs = SavingDetails.objects.filter(
            saving_date__range=[page_min_date, page_max_date],
        )
        if selected_employee is not None:
            loan_qs = loan_qs.filter(client__employee_for_id=selected_employee.id)
            saving_qs = saving_qs.filter(client__employee_for_id=selected_employee.id)

        for row in loan_qs.values('loan_return_date', 'client__employee_for_id').annotate(total=Sum('loan_return_amount')):
            loan_totals_map[(row['loan_return_date'], row['client__employee_for_id'])] = row['total']

        for row in saving_qs.values('saving_date', 'client__employee_for_id').annotate(total=Sum('saving_amount')):
            saving_totals_map[(row['saving_date'], row['client__employee_for_id'])] = row['total']

    loan_collection_details = []
    saving_collection_details = []
    for day in page_dates:
        day_str = str(day)
        for emp in target_employees:
            loan_collection_details.append({
                'date': day_str,
                'employee': emp,
                'total_collecton': {'loan_return_amount__sum': loan_totals_map.get((day, emp.id))},
            })
            saving_collection_details.append({
                'date': day_str,
                'employee': emp,
                'total_collecton': {'saving_amount__sum': saving_totals_map.get((day, emp.id))},
            })

    return {
        'loan_details': loan_collection_details,
        'saving_details': saving_collection_details,
        'all_employee': all_employee,
        'pagination_data_list': page_obj,
        'search_parameter': extract_search_parameter(request),
    }


def paginate_recent_entries(request, all_employee, loan_qs, saving_qs, per_page=DEFAULT_PAGE_SIZE):
    """Paginate loan and saving entry querysets with select_related and without clamping shorter side."""
    loan_qs = loan_qs.select_related('employee__user', 'client')
    saving_qs = saving_qs.select_related('employee__user', 'client')

    loan_paginator = Paginator(loan_qs, per_page)
    saving_paginator = Paginator(saving_qs, per_page)

    pagination_source = (
        loan_paginator.get_page(request.GET.get('page'))
        if loan_paginator.count >= saving_paginator.count
        else saving_paginator.get_page(request.GET.get('page'))
    )
    page_num = pagination_source.number

    loan_entries = loan_paginator.page(page_num) if page_num <= loan_paginator.num_pages else []
    saving_entries = saving_paginator.page(page_num) if page_num <= saving_paginator.num_pages else []

    return {
        'all_loan_entry': loan_entries,
        'all_savings_entry': saving_entries,
        'all_employee': all_employee,
        'pagination_data_list': pagination_source,
        'search_parameter': extract_search_parameter(request),
    }
