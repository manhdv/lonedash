import requests
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Account, Transaction, AccountBalance, Setting, Security
from .forms import AccountForm, TransactionForm

from .utils import recalc_account_balance_from_date

@login_required(login_url='login')
def transaction_create_api(request):
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


@csrf_exempt  # Hoặc dùng @csrf_protect nếu gọi từ JS có CSRF token
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
@login_required(login_url='login')
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


@login_required(login_url='login')
def account_create_api(request):
    if request.method == "POST":
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
    else:
        return HttpResponseNotAllowed(['POST'])



@csrf_exempt  # Hoặc dùng @csrf_protect nếu gọi từ JS có CSRF token
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
@login_required(login_url='login')
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