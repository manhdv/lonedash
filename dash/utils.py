from datetime import timedelta, timezone
from decimal import Decimal
from collections import defaultdict
from .models import AccountBalance, TradeExit, TradeEntry

def recalc_account_balance_from_date(account, start_date):
    # Lấy balance ngày trước start_date làm điểm khởi đầu
    prev_obj = AccountBalance.objects.filter(account=account, date__lt=start_date).order_by('-date').first()
    balance = prev_obj.balance if prev_obj else 0
    fee = prev_obj.fee if prev_obj else 0
    tax = prev_obj.tax if prev_obj else 0

    # Lấy transaction từ start_date trở đi
    transactions = account.transaction.filter(date__gte=start_date).order_by('date')

    # Lấy entry, exit từ start_date trở đi
    entries = account.entries.filter(date__gte=start_date).order_by('date')
    exits = TradeExit.objects.filter(entry__account=account, date__gte=start_date).order_by('date')

    daily_changes = defaultdict(Decimal)
    daily_fee = defaultdict(Decimal)
    daily_tax = defaultdict(Decimal)

    # Tổng hợp transaction vào daily_changes
    for tx in transactions:
        daily_changes[tx.date] += tx.net_amount()
        daily_fee[tx.date] += tx.fee
        daily_tax[tx.date] += tx.tax

    # Entry là mua -> trừ tiền (-net_amount)
    for entry in entries:
        net = entry.quantity * entry.price + entry.fee + entry.tax
        daily_changes[entry.date] -= net
        daily_fee[entry.date] += entry.fee
        daily_tax[entry.date] += entry.tax

    # Exit là bán -> cộng tiền (+net_amount)
    for exit in exits:
        gross = exit.quantity * exit.price
        net = gross - exit.fee - exit.tax
        daily_changes[exit.date] += net
        daily_fee[exit.date] += exit.fee
        daily_tax[exit.date] += exit.tax

    # Tính ngày bắt đầu, ngày kết thúc
    all_dates = set(daily_changes.keys())
    if not all_dates:
        # Không có giao dịch, fill balance từ start_date đến ngày hôm nay (hoặc 1 khoảng hợp lý)
        today = timezone.now().date()
        fill_date = max(start_date, today)  # fill đến ngày hôm nay hoặc start_date nếu start_date lớn hơn
        current_date = start_date
        while current_date <= fill_date:
            AccountBalance.objects.update_or_create(
                account=account,
                date=current_date,
                defaults={'balance': balance, 'fee': fee, 'tax': tax}
            )
            current_date += timedelta(days=1)
        return

    current_date = min(all_dates)
    last_date = max(all_dates)

    while current_date <= last_date:
        balance += daily_changes[current_date]
        fee += daily_fee[current_date]
        tax += daily_tax[current_date]

        AccountBalance.objects.update_or_create(
            account=account,
            date=current_date,
            defaults={'balance': balance, 'fee': fee, 'tax': tax}
        )
        current_date += timedelta(days=1)


def recalc_account_balance_from_date_old(account, start_date):
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