import requests
import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import get_object_or_404

from .models import Account, Transaction, AccountBalance, Setting, Security, Country, Trade
from .forms import AccountForm, TransactionForm, TradeForm

from .utils import recalc_account_balance_from_date

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
        recalc_account_balance_from_date(transaction.account, transaction.date)
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
    country_name = data.get('country')
    api_source = data.get('api_source')

    # Handle country
    try:
        country_obj = Country.objects.get(name=country_name)
    except Country.DoesNotExist:
        country_obj = Country.objects.get(name='Unknown')  # fallback

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

@require_http_methods(["DELETE"])
def security_update_api(request, id):
    securitiy = get_object_or_404(Security, id=id)
    if request.method == "DELETE":
        securitiy.delete()
        return JsonResponse({'success': True})

    else:
        return HttpResponseNotAllowed(['DELETE'])


@require_http_methods(["POST", "PUT"])
def trade_add_api(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'errors': 'Invalid JSON'}, status=400)

    form = TradeForm(data)
    if form.is_valid():
        trade = form.save(commit=False)
        trade.user = request.user
        trade.save()
        return JsonResponse({'status': 'ok'})
    else:
        print('Form errors:', form.errors.as_json())

        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)