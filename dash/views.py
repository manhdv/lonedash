from datetime import date
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Account, Transaction, Setting, Security, TradeEntry, TradeExit, AccountBalance, SecurityPrice, PortfolioPerformance
from .forms import AccountForm, TransactionForm, EntryForm, ExitForm

from django.db.models import Prefetch
from django.db.models import OuterRef, Subquery


# Create your views here.
def get_icons_svg():
    current_dir = os.path.dirname(__file__)
    svg_path = os.path.join(current_dir, 'static', 'icons', 'icons.svg')
    with open(svg_path, 'r', encoding='utf-8') as f:
        return f.read()


def dash_view(request):
    portfolio = PortfolioPerformance.objects.filter(user=request.user).order_by('date').last()
    
    return render(request, 'dash.html', {
        'icons_svg': get_icons_svg(),
        'portfolio': portfolio
    })

def accounts_view(request):
    balances_qs = AccountBalance.objects.filter(date__lte=date.today()).order_by('-date')
    accounts_list = Account.objects.filter(user=request.user).prefetch_related(
        Prefetch('balances', queryset=balances_qs, to_attr='prefetched_balances')
    ).order_by('id')

    for account in accounts_list:
        latest = next((b for b in account.prefetched_balances), None)
        account.balance = latest.balance if latest else 0
        account.principal = latest.principal if latest else 0
        account.equity = latest.equity if latest else 0
        account.fee = latest.fee if latest else 0
        account.tax = latest.tax if latest else 0

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

def transaction_edit_form(request, id):
    transaction = get_object_or_404(Transaction, id=id, user=request.user)
    form = TransactionForm(instance=transaction, user=request.user)
    return render(request, 'modals/transaction_modal.html', {
        'transaction_form': form
    })

def transaction_create_form(request):
    form = TransactionForm(user=request.user)
    return render(request, 'modals/transaction_modal.html', {
        'transaction_form': form
    })


def account_edit_form(request, id):
    account = get_object_or_404(Account, id=id)
    form = AccountForm(instance=account)
    return render(request, 'modals/account_modal.html', {
        'account_form': form
    })

def account_create_form(request):
    form = AccountForm()
    return render(request, 'modals/account_modal.html', {
        'account_form': form
    })


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
    return render(request, 'modals/account_modal.html', {'account_form': form})


def securities_view(request):
    # Subquery lấy giá close và date mới nhất cho mỗi security
    latest_prices = SecurityPrice.objects.filter(
        security=OuterRef('pk')
    ).order_by('-date')

    securities_list = Security.objects.filter(user=request.user).annotate(
        last_close=Subquery(latest_prices.values('close')[:1]),
        last_close_date=Subquery(latest_prices.values('date')[:1])
    ).order_by('-id')

    securities_paginator = Paginator(securities_list, 10)
    securities_page = securities_paginator.get_page(request.GET.get('page'))

    svg_content = get_icons_svg()
    return render(request, "securities.html", {
        'icons_svg': svg_content,
        'securities': securities_page,
    })


def trades_view(request):
    entries_list = TradeEntry.objects.filter(account__user=request.user).order_by('-id')
    entries_paginator = Paginator(entries_list, 10)
    entries_page = entries_paginator.get_page(request.GET.get('entries_page'))

    exits_list = TradeExit.objects.filter(entry__account__user=request.user).order_by('-id')
    exits_paginator = Paginator(exits_list, 10)
    exits_page = exits_paginator.get_page(request.GET.get('exits_page'))

    svg_content = get_icons_svg()
    return render(request, "trades.html", {'icons_svg': svg_content, 'entries' : entries_page, 'exits' : exits_page})

def entry_create_form(request):
    form = EntryForm()
    return render(request, 'modals/entry_modal.html', {
        'entry_form': form,
    })

def exit_create_form(request):
    form = ExitForm(user=request.user)
    return render(request, 'modals/exit_modal.html', {
        'exit_form': form,
    })

def settings_view(request):
    obj, _ = Setting.objects.get_or_create(user=request.user)
    if request.method == "POST":
        obj.key_yahoo = request.POST.get('key_yahoo', '').strip()
        obj.key_eodhd = request.POST.get('key_eodhd', '').strip()
        obj.save()
        return redirect('settings') 
    svg_content = get_icons_svg()
    return render(request, "settings.html", {'icons_svg': svg_content, 'key_yahoo': obj.key_yahoo, 'key_eodhd': obj.key_eodhd,})

def security_search_form(request):
    return render(request, 'modals/search_modal.html')