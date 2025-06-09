from decimal import Decimal
import requests
import json

from django.http import HttpResponseNotAllowed, JsonResponse
from django.views.decorators.http import require_POST, require_http_methods

from django.shortcuts import get_object_or_404

from .models import Account, Transaction, Setting, Security, Country, TradeEntry, TradeExit, PortfolioPerformance
from .forms import AccountForm, TransactionForm, EntryForm, ExitForm
from .utils import update_account, update_security_prices_for_user

from collections import defaultdict


@require_POST
def transaction_create_api(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

    form = TransactionForm(data, user=request.user)
    if form.is_valid():
        transaction = form.save(commit=False)
        transaction.user = request.user
        transaction.save()
        update_account(transaction.account, transaction.date)
        return JsonResponse({'success': True, 'id': transaction.id})
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def transaction_update_api(request, id):
    transaction = get_object_or_404(Transaction, id=id, user=request.user)

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
            update_account(updated_transaction.account, min_date)
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
        update_account(account, recalc_date)
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['PUT', 'PATCH', 'DELETE'])


@require_POST
def account_create_api(request):
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
def account_update_api(request, id):
    account = get_object_or_404(Account, id=id)

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

def security_search_api(request):
    q = request.GET.get('q', '')
    if not q:
        return JsonResponse({'error': 'Missing query'}, status=400)

    user = request.user
    try:
        setting = Setting.objects.get(user=user)
    except Setting.DoesNotExist:
        return JsonResponse({'error': 'No API keys configured'}, status=500)

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
        eodhd_key = setting.key_eodhd
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


def security_add_api(request):
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

    update_security_prices_for_user(request.user)
    return JsonResponse({'status': 'ok' if created else 'exists'})

@require_http_methods(["DELETE"])
def security_update_api(request, id):
    securitiy = get_object_or_404(Security, id=id)
    if request.method == "DELETE":
        securitiy.delete()
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['DELETE'])


@require_http_methods(["POST", "PUT"])
def entry_add_api(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'errors': 'Invalid JSON'}, status=400)

    form = EntryForm(data)
    if form.is_valid():
        entry = form.save(commit=False)
        entry.save()

        update_account(entry.account, entry.date)
        return JsonResponse({'status': 'ok'})
    else:
        print('Form errors:', form.errors.as_json())

        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def entry_update_api(request, id):
    entry = get_object_or_404(TradeEntry, id=id)

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
            update_account(updated_entry.account, min_date)
            return JsonResponse({'success': True, 'id': entry.id})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    elif request.method == "DELETE":
        entry.delete()
        update_account(entry.account, entry.date)
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['PUT', 'PATCH', 'DELETE'])


def portfolio_chart_api(request):
    # performance series
    perf_qs = PortfolioPerformance.objects.filter(
        user=request.user
    ).order_by('date')

    # lấy list ngày để map cho lẹ
    dates = [p.date for p in perf_qs]

    # ----‑ transactions ----‑
    tx_map = defaultdict(Decimal)
    tx_qs = Transaction.objects.filter(
        account__user=request.user,
        date__in=dates
    )
    for tx in tx_qs:
        tx_map[tx.date] += tx.net_amount()   # net_amount() đã +/- sẵn

    # ----‑ build JSON ----‑
    chart_data = {
        "labels":      [d.strftime('%Y-%m-%d') for d in dates],
        "principal":   [float(p.principal) for p in perf_qs],
        "equity":      [float(p.equity)    for p in perf_qs],
        "transactions":[float(tx_map.get(d, 0)) for d in dates],
    }
    return JsonResponse(chart_data)

@require_http_methods(["POST", "PUT"])
def exit_add_api(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'errors': 'Invalid JSON'}, status=400)

    form = ExitForm(data, user=request.user)
    if form.is_valid():
        exit = form.save(commit=False)
        exit.save()
        
        update_account(exit.entry.account, exit.date)
        return JsonResponse({'status': 'ok'})
    else:
        print('Form errors:', form.errors.as_json())

        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def exit_update_api(request, id):
    exit = get_object_or_404(TradeExit, id=id)

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
            update_account(updated_exit.account, min_date)
            return JsonResponse({'success': True, 'id': exit.id})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    elif request.method == "DELETE":
        exit.delete()
        update_account(exit.entry.account, exit.date)
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['PUT', 'PATCH', 'DELETE'])
