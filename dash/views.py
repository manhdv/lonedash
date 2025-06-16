from datetime import date
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Account, Transaction, UserAPIKey, Security, TradeEntry, TradeExit, AccountBalance, SecurityPrice, PortfolioPerformance, UserAPIKey, UserPreference, Currency, Language
from .forms import AccountForm, TransactionForm, EntryForm, ExitForm

from django.db.models import Prefetch
from django.db.models import OuterRef, Subquery

from .utils import utils_calculate_drawdown, utils_calculate_twrr, utils_recalc_from, utils_recalc_daily_holdings
from django.db.models import Min


from django.db.models import Sum, F, Q

# Create your views here.
def get_icons_svg():
    current_dir = os.path.dirname(__file__)
    svg_path = os.path.join(current_dir, 'static', 'icons', 'icons.svg')
    with open(svg_path, 'r', encoding='utf-8') as f:
        return f.read()


def dash_view(request):
    data = PortfolioPerformance.objects.filter(user=request.user).order_by('date')

    portfolio = data.last()
    max_dd = utils_calculate_drawdown(data)
    twrr = utils_calculate_twrr(data)
    currency_symbol = request.user.userpreference.currency.symbol
    return render(request, 'dash.html', {
        'icons_svg': get_icons_svg(),
        'portfolio': portfolio,
        'max_dd' : max_dd,
        'twrr': twrr,
        'currency_symbol': currency_symbol,
        'active_page': "dashboard"
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
        'active_page': "accounts"
    })

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect(request.GET.get('next', 'dashboard'))

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
        'active_page': "securities"
    })


def trades_view(request):
    entries_list = TradeEntry.objects.filter(account__user=request.user).order_by('-id')
    entries_paginator = Paginator(entries_list, 10)
    entries_page = entries_paginator.get_page(request.GET.get('entries_page'))

    exits_list = TradeExit.objects.filter(entry__account__user=request.user).order_by('-id')
    exits_paginator = Paginator(exits_list, 10)
    exits_page = exits_paginator.get_page(request.GET.get('exits_page'))

    svg_content = get_icons_svg()
    return render(request, "trades.html", {
        'icons_svg': svg_content, 
        'entries' : entries_page, 
        'exits' : exits_page,
        'active_page': "trades"
        })

def entry_create_form(request):
    form = EntryForm()
    return render(request, 'modals/entry_modal.html', {
        'entry_form': form,
    })

def entry_edit_form(request, id):
    entry = get_object_or_404(TradeEntry, id=id)
    form = EntryForm(instance=entry)
    return render(request, 'modals/entry_modal.html', {
        'entry': entry,
        'entry_form': form
    })

def exit_create_form(request):

    open_entries = TradeEntry.objects.annotate(
        filled=Sum('exits__quantity')
    ).filter(
        Q(filled__lt=F('quantity')) | Q(filled__isnull=True)
    )
    form = ExitForm(open_entries=open_entries)
    return render(request, 'modals/exit_modal.html', {
        'exit_form': form,
    })

def exit_edit_form(request, id):
    exit = get_object_or_404(TradeExit, id=id)
    form = ExitForm(instance=exit)
    return render(request, 'modals/exit_modal.html', {
        'exit': exit,
        'exit_form': form
    })

def settings_view(request):
    user = request.user
    api_keys, _ = UserAPIKey.objects.get_or_create(user=user)
    user_pref, _ = UserPreference.objects.get_or_create(user=user)

    print(f"[INFO] Setting_view called")

    if request.method == "POST":
        api_keys.key_eodhd = request.POST.get("key_eodhd", "").strip()
        api_keys.key_finhub = request.POST.get("key_finhub", "").strip()
        api_keys.key_alpha_vantage = request.POST.get("key_alpha_vantage", "").strip()
        api_keys.key_yahoo = request.POST.get("key_yahoo", "").strip()
        api_keys.save()

        print(f"[INFO] Setting_view POST")

        # Track if currency changed
        try:
            new_currency_id = int(request.POST.get("currency"))
        except (TypeError, ValueError):
            new_currency_id = None

        current_currency_id = UserPreference.objects.get(user=user).currency.id
        print(f"[DEBUG] Submitted currency: {new_currency_id}")
        print(f"[DEBUG] Current user_pref.currency_id: {current_currency_id}")
        user_pref.language_id = request.POST.get("language") or None
        user_pref.currency_id = request.POST.get("currency") or None
        user_pref.save()
        if str(current_currency_id) != str(new_currency_id):

            print(f"[INFO] User {user.id} changed currency from {current_currency_id} to {new_currency_id}")

            # Find the latest performance date
            earliest_date = (
                PortfolioPerformance.objects
                .filter(user=user)
                .aggregate(Min("date"))["date__min"]
            )

            print(f"[DEBUG] Earliest portfolio performance date: {earliest_date}")

            if earliest_date:
                print(f"[INFO] Recalculating portfolio for user {user.id} as of {earliest_date}")
                utils_recalc_from(user, earliest_date)
            else:
                print(f"[WARN] No portfolio performance found for user {user.id}, skipping recalculation")
        else:
            print(f"[INFO] Currency not changed for user {user.id}, skipping recalculation")




        return redirect("settings")

    return render(request, "settings.html", {
        "key_eodhd": api_keys.key_eodhd,
        "key_finhub": api_keys.key_finhub,
        "key_alpha_vantage": api_keys.key_alpha_vantage,
        'icons_svg': get_icons_svg(),
        "languages": Language.objects.all(),
        "currencies": Currency.objects.all(),
        "current_lang": user_pref.language_id,
        "current_currency": user_pref.currency_id,
    })


def security_search_form(request):
    return render(request, 'modals/search_modal.html')


def holdings_view(request):
    return render(request, 'holdings.html', {'active_page': "holdings"})