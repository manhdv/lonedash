from decimal import Decimal
import requests
import json
from collections import defaultdict, OrderedDict
from django.core.cache import cache

from django.http import HttpResponseNotAllowed, JsonResponse
from django.views.decorators.http import require_POST, require_http_methods

from django.shortcuts import get_object_or_404

from .models import Account, Transaction, Security, Country, TradeEntry, TradeExit, PortfolioPerformance, UserAPIKey, UserPreference, DailyHoldingEquity
from .forms import AccountForm, TransactionForm, EntryForm, ExitForm
from .utils import utils_update_account, utils_update_security_prices_for_user, utils_convert_currency, utils_recalc_daily_holdings



@require_POST
def api_transaction_create(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

    form = TransactionForm(data, user=request.user)
    if form.is_valid():
        transaction = form.save(commit=False)
        transaction.user = request.user
        transaction.save()
        utils_update_account(transaction.account, transaction.date)
        return JsonResponse({'success': True, 'id': transaction.id})
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def api_transaction_update(request, id):
    transaction = get_object_or_404(Transaction, id=id, user=request.user)

        # Crucial: Check if the requesting user owns the entry
    if transaction.user != request.user: # Assuming TradeEntry has a 'user' ForeignKey
        return JsonResponse({'success': False, 'errors': 'Not authorized'}, status=403) # Forbidden

    if request.method in ["PUT", "PATCH"]:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

        old_date = transaction.date  # lấy ngày trước khi update

        form = TransactionForm(data, instance=transaction, user=request.user)
        if form.is_valid():
            updated_transaction = form.save()
            min_date = min(old_date, updated_transaction.date)
            utils_update_account(updated_transaction.account, min_date)
            # Debug output
            print("=== Transaction Update Debug ===")
            print("Old date:", old_date)
            print("New date:", updated_transaction.date)
            print("Max date used:", min_date)
            print("Account ID:", updated_transaction.account.id)
            print("Account Name:", updated_transaction.account.name)  # assuming there's a name field
            print("================================")
            return JsonResponse({'success': True, 'id': transaction.id})

    elif request.method == "DELETE":
        recalc_date = transaction.date
        account = transaction.account
        transaction.delete()
        utils_update_account(account, recalc_date)
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['PUT', 'PATCH', 'DELETE'])


@require_POST
def api_account_create(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

    form = AccountForm(data)
    if form.is_valid():
        account = form.save(commit=False)
        account.user = request.user
        account.save()
        return JsonResponse({'success': True, 'id': account.id})
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)



@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def api_account_update(request, id):
    account = get_object_or_404(Account, id=id)

    # Crucial: Check if the requesting user owns the entry
    if account.user != request.user: # Assuming TradeEntry has a 'user' ForeignKey
        return JsonResponse({'success': False, 'errors': 'Not authorized'}, status=403) # Forbidden

    if request.method in ["PUT", "PATCH"]:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

        form = AccountForm(data, instance=account)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'id': account.id})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    elif request.method == "DELETE":
        account.delete()
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['PUT', 'PATCH', 'DELETE'])

def api_security_search(request):
    q = request.GET.get('q', '')
    if not q:
        return JsonResponse({'error': 'Missing query'}, status=400)
    
    yahoo_results = []
    eodhd_results = []

    # Yahoo
    try:
        yahoo_url = 'https://query1.finance.yahoo.com/v1/finance/search'
        yahoo_headers = {'User-Agent': 'Mozilla/5.0'}
        yahoo_resp = requests.get(yahoo_url, params={'q': q}, headers=yahoo_headers, timeout=5, verify=False)
        if yahoo_resp.ok != 200:
            print(f"Yahoo respond OK")
            yahoo_data = yahoo_resp.json()
            yahoo_results = yahoo_data.get('quotes', [])
    except Exception as e:
        print('Yahoo API error:', e)

    print(f"Yahoo results: {len(yahoo_results)}")
    # EODHD
    try:
        user_api, _ = UserAPIKey.objects.get_or_create(user=request.user)
        eodhd_key = user_api.key_eodhd
        if eodhd_key:
            eodhd_url = f'https://eodhd.com/api/search/{q}'
            eodhd_params = {'api_token': eodhd_key, 'limit': 20, 'fmt': 'json'}
            eodhd_resp = requests.get(eodhd_url, params=eodhd_params, timeout=5, verify=False)
            if eodhd_resp.ok:
                print(f"EODHD respond OK")
                eodhd_results = eodhd_resp.json()
    except Exception as e:
        print('EODHD API error:', e)
    print(f"EODHD results: {len(eodhd_results)}")
    return JsonResponse({'yahoo': yahoo_results, 'eodhd': eodhd_results})


def api_security_add(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    code = data.get('code')
    exchange = data.get('exchange')
    name = data.get('name')
    type_ = data.get('type')
    api_source = data.get('api_source')

    security, created = Security.objects.get_or_create(
        user=request.user,
        code=code,
        defaults={
            'exchange': exchange,
            'name': name,
            'type': type_,
            'api_source': api_source,
        }
    )

    utils_update_security_prices_for_user(request.user)
    return JsonResponse({'status': 'ok' if created else 'exists'})

@require_http_methods(["DELETE"])
def api_security_update(request, id):
    securitiy = get_object_or_404(Security, id=id)

    # Crucial: Check if the requesting user owns the entry
    if securitiy.user != request.user: # Assuming TradeEntry has a 'user' ForeignKey
        return JsonResponse({'success': False, 'errors': 'Not authorized'}, status=403) # Forbidden
    
    if request.method == "DELETE":
        securitiy.delete()
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['DELETE'])


@require_http_methods(["POST", "PUT"])
def api_entry_add(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'errors': 'Invalid JSON'}, status=400)

    form = EntryForm(data)
    if form.is_valid():
        entry = form.save(commit=False)
        entry.save()

        utils_update_account(entry.account, entry.date)
        utils_recalc_daily_holdings(user=request.user,security= entry.security,from_date= entry.date)
        return JsonResponse({'status': 'ok'})
    else:
        print('Form errors:', form.errors.as_json())

        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def api_entry_update(request, id):
    entry = get_object_or_404(TradeEntry, id=id)
    # Crucial: Check if the requesting user owns the entry
    if entry.user != request.user: # Assuming TradeEntry has a 'user' ForeignKey
        return JsonResponse({'success': False, 'errors': 'Not authorized'}, status=403) # Forbidden
    
    if request.method in ["PUT", "PATCH"]:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

        old_date = entry.date  # lấy ngày cũ trước khi save

        form = EntryForm(data, instance=entry)
        if form.is_valid():
            updated_entry = form.save()
            min_date = min(old_date, updated_entry.date)
            utils_update_account(updated_entry.account, min_date)
            utils_recalc_daily_holdings(user=request.user,security= entry.security,from_date= min_date)
            return JsonResponse({'success': True, 'id': entry.id})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    elif request.method == "DELETE":
        entry.delete()
        utils_update_account(entry.account, entry.date)
        utils_recalc_daily_holdings(user=request.user,security= entry.security,from_date= entry.date)
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['PUT', 'PATCH', 'DELETE'])


def api_portfolio_chart(request):
    user = request.user
    cache_key = f"portfolio_chart_{user.id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    perf_qs = PortfolioPerformance.objects.filter(user=user).order_by("date")
    dates = [p.date for p in perf_qs]

    chart_data = {
        "labels": [d.strftime('%Y-%m-%d') for d in dates],
        "principal": [float(p.principal) for p in perf_qs],
        "equity": [float(p.equity) for p in perf_qs],
        "transactions": [float(p.transaction) for p in perf_qs],
    }

    cache.set(cache_key, chart_data, timeout=3600)  # Cache data in 1 hour
    return JsonResponse(chart_data)

@require_http_methods(["POST", "PUT"])
def api_exit_add(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'errors': 'Invalid JSON'}, status=400)

    form = ExitForm(data)



    if form.is_valid():
        exit = form.save(commit=False)
        # Crucial: Check if the requesting user owns the entry
        if exit.entry.account.user != request.user: # Assuming TradeEntry has a 'user' ForeignKey
            return JsonResponse({'success': False, 'errors': 'Not authorized'}, status=403) # Forbidden

        exit.save()
       
        utils_update_account(exit.entry.account, exit.date)
        utils_recalc_daily_holdings(user=request.user,security= exit.security,from_date= exit.date)
        return JsonResponse({'status': 'ok'})
    else:
        print('Form errors:', form.errors.as_json())

        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def api_exit_update(request, id):
    exit = get_object_or_404(TradeExit, id=id)

    # Crucial: Check if the requesting user owns the entry
    if exit.entry.account.user != request.user: # Assuming TradeEntry has a 'user' ForeignKey
        return JsonResponse({'success': False, 'errors': 'Not authorized'}, status=403) # Forbidden
    
    if request.method in ["PUT", "PATCH"]:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

        old_date = exit.date  # lấy ngày cũ trước khi save

        form = ExitForm(data, instance=exit)
        if form.is_valid():
            updated_exit = form.save()
            min_date = min(old_date, updated_exit.date)
            utils_update_account(updated_exit.account, min_date)
            utils_recalc_daily_holdings(user=request.user,security= exit.security,from_date= min_date)
            return JsonResponse({'success': True, 'id': exit.id})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    elif request.method == "DELETE":
        exit.delete()
        utils_update_account(exit.entry.account, exit.date)
        utils_recalc_daily_holdings(user=request.user,security= exit.security,from_date= exit.date)
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['PUT', 'PATCH', 'DELETE'])

def api_holdings_data(request):
    user = request.user
    cache_key = f"holdings_data_{user.id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    target_currency = UserPreference.objects.get(user=user).currency.code
    records = DailyHoldingEquity.objects.filter(user=user).order_by("date")

    if not records.exists():
        return JsonResponse([], safe=False)

    date_list = sorted(set(r.date.strftime("%Y-%m-%d") for r in records))
    result = defaultdict(lambda: OrderedDict())

    for r in records:
        equity = r.equity
        if r.currency != target_currency:
            equity *= utils_convert_currency(r.currency, target_currency, r.date)

        date_str = r.date.strftime("%Y-%m-%d")
        result[r.security.code][date_str] = float(equity)

    datasets = {
        code: [data.get(date, 0) for date in date_list]
        for code, data in result.items()
    }

    chart_data = {
        "labels": date_list,
        "datasets": datasets
    }

    # Cache for 1 hour (3600s) — tweak as needed
    cache.set(cache_key, chart_data, timeout=3600)

    return JsonResponse(chart_data)
