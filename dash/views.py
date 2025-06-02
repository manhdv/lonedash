from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max, Sum, Case, When, F, DecimalField
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from dash.models import EconomicData, Country
from .models import Account, Transaction, AccountBalance
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
    form = AccountForm()
    if request.method == 'POST':
        if 'account_submit' in request.POST:
            form = AccountForm(request.POST)
            if form.is_valid():
                new_account = form.save(commit=False)
                new_account.user = request.user
                new_account.save()
                return redirect('accounts')  # 🔁 redirect tránh resubmit

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
        'form': form,
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
@require_POST
def transaction_delete(request):
    tx_id = request.POST.get("transaction_id")
    transaction = get_object_or_404(Transaction, id=tx_id, user=request.user)
    transaction.delete()
    recalc_account_balance_from_date(transaction.account, transaction.date)
    return redirect('accounts')

@login_required(login_url='login')
def transaction_new(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            recalc_account_balance_from_date(transaction.account, transaction.date)
            return redirect('accounts')
        else:
            # re-render the modal with errors
            return render(request, 'transaction_modal.html', {'transaction_form': form})
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'transaction_modal.html', {'transaction_form': form})

@login_required(login_url='login')
def transaction_edit(request, tx_id):
    transaction = get_object_or_404(Transaction, id=tx_id, user=request.user)
    if request.method == "POST":
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            recalc_account_balance_from_date(transaction.account, transaction.date)
            print ("render edit ok")
            return redirect('accounts')
        else:
            print ("render edit error")
            return render(request, 'transaction_modal.html', {'transaction_form': form})
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    return render(request, 'transaction_modal.html', {'transaction_form': form})
