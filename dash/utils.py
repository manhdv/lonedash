from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
from .models import Account, Transaction, AccountBalance, Setting, Security
from .forms import AccountForm, TransactionForm

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
