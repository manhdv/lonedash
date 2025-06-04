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
def transaction_edit_form(request, id):
    transaction = get_object_or_404(Transaction, id=id, user=request.user)
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


@login_required(login_url='login')
def account_edit_form(request, id):
    account = get_object_or_404(Account, id=id)
    form = AccountForm(instance=account)
    return render(request, 'account_modal.html', {
        'account_form': form
    })

@login_required(login_url='login')
def account_create_form(request):
    form = AccountForm()
    return render(request, 'account_modal.html', {
        'account_form': form
    })



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