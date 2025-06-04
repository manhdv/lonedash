from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
import os
import requests
import json


from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max, Sum, Case, When, F, DecimalField
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST,require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .models import EconomicData, Country
from .models import Account, Transaction, AccountBalance, Setting, Security
from .forms import AccountForm, TransactionForm


# Create your views here.
def get_icons_svg():
    current_dir = os.path.dirname(__file__)
    svg_path = os.path.join(current_dir, 'static', 'icons', 'icons.svg')
    with open(svg_path, 'r', encoding='utf-8') as f:
        return f.read()

def recalc_account_balance_from_date(account, start_date):
    # Lấy tất cả transaction từ start_date trở đi, theo ngày tăng dần
    transactions = account.transaction.filter(date__gte=start_date).order_by('date')

    # Lấy balance ngày trước start_date để làm điểm xuất phát
    prev_obj = AccountBalance.objects.filter(account=account, date__lt=start_date).order_by('-date').first()
    balance = prev_obj.balance if prev_obj else 0
    fee = prev_obj.fee if prev_obj else 0
    tax = prev_obj.tax if prev_obj else 0


    # Dùng dict để cộng balance theo từng ngày
    daily_changes = defaultdict(Decimal)
    daily_fee = defaultdict(Decimal)
    daily_tax = defaultdict(Decimal)
    for tx in transactions:
        daily_changes[tx.date] += tx.net_amount()
        daily_fee[tx.date] += tx.fee
        daily_tax[tx.date] += tx.tax

    # Tính balance theo ngày tuần tự từ start_date đến ngày cuối cùng có transaction
    current_date = start_date
    last_date = transactions.last().date if transactions.exists() else start_date

    while current_date <= last_date:
        balance += daily_changes[current_date]  # cộng thay đổi ngày hiện tại (0 nếu ko có)
        fee += daily_fee[current_date]
        tax += daily_tax[current_date]
        AccountBalance.objects.update_or_create(
            account=account,
            date=current_date,
            defaults={'balance': balance, 'fee': fee, 'tax': tax}
        )
        current_date += timedelta(days=1)

@login_required(login_url='login')
def dash_view(request):
    return render(request, 'dash.html', {'icons_svg': get_icons_svg()})

@login_required(login_url='login') 
def accounts_view(request):
    accounts_list = Account.objects.filter(user=request.user).prefetch_related('balances').order_by('id')
    for account in accounts_list:
        latest = (
            account.balances
            .filter(date__lte=date.today())
            .order_by('-date')
            .first()
        )
        account.last_balance = latest.balance if latest else 0
        account.last_fee = latest.fee if latest else 0
        account.last_tax = latest.tax if latest else 0

    paginator = Paginator(accounts_list, 10)  # 10 per page
    page_number = request.GET.get('page')
    accounts_page = paginator.get_page(page_number) 

    transaction_list = Transaction.objects.filter(user=request.user).order_by('-id')
    transactions_paginator = Paginator(transaction_list, 10)
    transactions_page = transactions_paginator.get_page(request.GET.get('txn_page'))

    svg_content = get_icons_svg()

    return render(request, 'accounts.html', {
        'accounts': accounts_page,
        'transactions' : transactions_page,
        'icons_svg': svg_content,
    })

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect(request.GET.get('next', 'accounts'))

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def transaction_new(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

        form = TransactionForm(data, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            recalc_account_balance_from_date(transaction.account, transaction.date)
            return JsonResponse({'success': True, 'id': transaction.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        return HttpResponseNotAllowed(['POST'])


@login_required(login_url='login')
def transaction_edit_form(request, tx_id):
    transaction = get_object_or_404(Transaction, id=tx_id, user=request.user)
    form = TransactionForm(instance=transaction, user=request.user)
    return render(request, 'transaction_modal.html', {
        'transaction_form': form
    })

@login_required(login_url='login')
def transaction_create_form(request):
    form = TransactionForm(user=request.user)
    return render(request, 'transaction_modal.html', {
        'transaction_form': form
    })

@csrf_exempt  # Hoặc dùng @csrf_protect nếu gọi từ JS có CSRF token
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
@login_required(login_url='login')
def transaction_update(request, tx_id):
    transaction = get_object_or_404(Transaction, id=tx_id, user=request.user)

    if request.method in ["PUT", "PATCH"]:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

        form = TransactionForm(data, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            recalc_account_balance_from_date(transaction.account, transaction.date)
            return JsonResponse({'success': True, 'id': transaction.id})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    elif request.method == "DELETE":
        recalc_date = transaction.date
        account = transaction.account
        transaction.delete()
        recalc_account_balance_from_date(account, recalc_date)
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['PUT', 'PATCH', 'DELETE'])

@login_required(login_url='login')
@require_POST
def account_delete(request):
    acc_id = request.POST.get("account_id")
    account = get_object_or_404(Account, id=acc_id, user=request.user)
    account.delete()
    return redirect('accounts')

@login_required(login_url='login')
def account_new(request):
    if request.method == "POST":
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            return JsonResponse({'success': True, 'id': account.id})
        else:
            # re-render the modal with errors
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = AccountForm()
    return render(request, 'account_modal.html', {'account_form': form})

@login_required(login_url='login')
def account_edit(request, acc_id):
    account = get_object_or_404(Account, id=acc_id, user=request.user)
    if request.method == "POST":
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'id': account.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = AccountForm(instance=account)
    return render(request, 'account_modal.html', {'account_form': form})


@login_required(login_url='login') 
def securities_view(request):
    securities_list = Security.objects.filter(user=request.user).order_by('-id')
    securities_paginator = Paginator(securities_list, 10)
    securities_page = securities_paginator.get_page(request.GET.get('page'))

    svg_content = get_icons_svg()
    return render(request, "securities.html", {'icons_svg': svg_content, 'securities' : securities_page,})

@login_required(login_url='login') 
def securities_search(request):
    q = request.GET.get('q', '')
    if not q:
        return JsonResponse({'error': 'Missing query parameter'}, status=400)

    url = 'https://query1.finance.yahoo.com/v1/finance/search'
    params = {'q': q}
    headers = {
        'User-Agent': 'Mozilla/5.0'  # fake UA tránh bị block
    }

    resp = requests.get(url, params=params, headers=headers, verify=False)
    if resp.status_code != 200:
        return JsonResponse({'error': 'Yahoo API error'}, status=resp.status_code)

    return JsonResponse(resp.json())


@require_POST
@login_required(login_url='login') 
def securities_add(request):
    data = request.POST
    code = data.get('code')
    exchange = data.get('exchange')
    name = data.get('name')
    type_ = data.get('type')
    country_name = data.get('country')
    api_source = data.get('api_source')

    # Handle country
    country_obj, _ = Country.objects.get_or_create(name=country_name or 'Unknown')

    security, created = Security.objects.get_or_create(
        user=request.user,
        code=code,
        defaults={
            'exchange': exchange,
            'name': name,
            'type': type_,
            'country': country_obj,
            'api_source': api_source,
        }
    )
    return JsonResponse({'status': 'ok' if created else 'exists'})

@login_required(login_url='login') 
def settings_view(request):
    obj, _ = Setting.objects.get_or_create(user=request.user)
    if request.method == "POST":
        obj.key_yahoo = request.POST.get('key_yahoo', '').strip()
        obj.key_eodhd = request.POST.get('key_eodhd', '').strip()
        obj.save()
        return redirect('settings') 
    svg_content = get_icons_svg()
    return render(request, "settings.html", {'icons_svg': svg_content, 'key_yahoo': obj.key_yahoo, 'key_eodhd': obj.key_eodhd,})