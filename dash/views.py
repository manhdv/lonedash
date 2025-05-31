from django.shortcuts import render, redirect
from dash.models import EconomicData, Country
from django.db.models import Max
import os
from .models import Account, Transaction, AccountBalance
from .forms import AccountForm, TransactionForm
from django.db.models import Sum, Case, When, F, DecimalField
from collections import defaultdict
from datetime import timedelta, date

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout


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
    prev_balance_obj = AccountBalance.objects.filter(account=account, date__lt=start_date).order_by('-date').first()
    balance = prev_balance_obj.balance if prev_balance_obj else 0

    # Dùng dict để cộng balance theo từng ngày
    daily_changes = defaultdict(Decimal)
    for tx in transactions:
        amt = tx.amount if tx.type in ['deposit', 'transfer_in', 'dividien', 'interest'] else -tx.amount
        daily_changes[tx.date] += amt

    # Tính balance theo ngày tuần tự từ start_date đến ngày cuối cùng có transaction
    current_date = start_date
    last_date = transactions.last().date if transactions.exists() else start_date

    while current_date <= last_date:
        balance += daily_changes[current_date]  # cộng thay đổi ngày hiện tại (0 nếu ko có)
        AccountBalance.objects.update_or_create(
            account=account,
            date=current_date,
            defaults={'balance': balance}
        )
        current_date += timedelta(days=1)

@login_required(login_url='login')
def dash_view(request):
    return render(request, 'dash.html', {'icons_svg': get_icons_svg()})

@login_required(login_url='login') 
def accounts_view(request):
    form = AccountForm()
    t_form = TransactionForm(user=request.user)

    if request.method == 'POST':
        if 'account_submit' in request.POST:
            form = AccountForm(request.POST)
            if form.is_valid():
                new_account = form.save(commit=False)
                new_account.user = request.user
                new_account.save()
                return redirect('accounts')  # 🔁 redirect tránh resubmit
        elif 'transaction_submit' in request.POST:
            t_form = TransactionForm(request.POST, user=request.user)
            if t_form.is_valid():
                transaction = t_form.save(commit=False)
                transaction.user = request.user
                transaction.save()
                recalc_account_balance_from_date(transaction.account, transaction.date)
                return redirect('accounts')

    # GET hoặc invalid form vẫn đến đây
    accounts = Account.objects.filter(user=request.user).prefetch_related('balances')
    for account in accounts:
        # lọc balance trước hoặc bằng hôm nay, lấy ngày mới nhất
        latest_balance = (
            account.balances
            .filter(date__lte=date.today())
            .order_by('-date')
            .first()
        )
        account.last_balance = latest_balance.balance if latest_balance else 0
    transactions = Transaction.objects.filter(user=request.user)
    svg_content = get_icons_svg()

    return render(request, 'accounts.html', {
        'accounts': accounts,
        'transactions' : transactions,
        'form': form,
        'transaction_form': t_form,
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
