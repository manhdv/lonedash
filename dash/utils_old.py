from datetime import timedelta, datetime, date as dt_date
from decimal import Decimal
from collections import defaultdict
from .models import AccountBalance, TradeExit, TradeEntry, SecurityPrice

def update_account_balance(account, start_date):
    # Lấy balance ngày trước start_date làm điểm khởi đầu
    prev_obj = AccountBalance.objects.filter(account=account, date__lt=start_date).order_by('-date').first()
    balance = prev_obj.balance if prev_obj else 0
    fee = prev_obj.fee if prev_obj else 0
    tax = prev_obj.tax if prev_obj else 0
    principal = prev_obj.principal if prev_obj else 0
    # Lấy transaction từ start_date trở đi
    transactions = account.transaction.filter(date__gte=start_date).order_by('date')

    # Lấy entry, exit từ start_date trở đi
    entries = account.entries.filter(date__gte=start_date).order_by('date')
    exits = TradeExit.objects.filter(entry__account=account, date__gte=start_date).order_by('date')

    daily_changes = defaultdict(Decimal)
    daily_fee = defaultdict(Decimal)
    daily_tax = defaultdict(Decimal)
    daily_principal_change = defaultdict(Decimal)

    # Tổng hợp transaction vào daily_changes
    for tx in transactions:
        daily_changes[tx.date] += tx.net_amount()
        daily_fee[tx.date] += tx.fee
        daily_tax[tx.date] += tx.tax
        # Nếu transaction là nạp tiền (deposit), cộng vào principal
        if tx.type == 'deposit':
            daily_principal_change[tx.date] += tx.net_amount()
        # Nếu transaction là rút tiền (withdraw), trừ khỏi principal
        elif tx.type == 'withdraw':
            daily_principal_change[tx.date] -= tx.net_amount()

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
    all_dates = set(daily_changes.keys()) | set(daily_principal_change.keys())
    if not all_dates:
        # Không có giao dịch, fill balance từ start_date đến ngày hôm nay (hoặc 1 khoảng hợp lý)
        today = dt_date.today()
        fill_date = max(start_date, today)  # fill đến ngày hôm nay hoặc start_date nếu start_date lớn hơn
        current_date = start_date
        while current_date <= fill_date:
            AccountBalance.objects.update_or_create(
                account=account,
                date=current_date,
                defaults={'balance': balance, 'fee': fee, 'tax': tax, 'principal': principal}
            )
            current_date += timedelta(days=1)
        return

    current_date = min(all_dates)
    today = dt_date.today()
    last_date = max(today, max(all_dates))  # ép phải chạy đến hôm nay

    while current_date <= last_date:
        balance += daily_changes[current_date]
        fee += daily_fee[current_date]
        tax += daily_tax[current_date]
        principal += daily_principal_change[current_date]

        AccountBalance.objects.update_or_create(
            account=account,
            date=current_date,
            defaults={'balance': balance, 'fee': fee, 'tax': tax, 'principal': principal}
        )
        current_date += timedelta(days=1)


def update_account_float(account, start_date):
    today = dt_date.today()
    current = start_date

    while current <= today:
        update_account_float_date(account, current)
        current += timedelta(days=1)

def update_account_float_date(account, date):
    # Lấy tất cả entries mua <= date
    entries = TradeEntry.objects.filter(account=account)

    # Tính tổng quantity còn giữ theo security
    security_quantities = {}
    for entry in entries:
        remaining = entry.remaining_quantity(until_date=date)
        if remaining > 0:
            security_quantities[entry.security_id] = security_quantities.get(entry.security_id, Decimal('0')) + remaining

    # Lấy giá close từng security vào date
    prices = SecurityPrice.objects.filter(security_id__in=security_quantities.keys(), date=date)
    price_map = {p.security_id: p.close for p in prices}

    def get_latest_price_before(security_id, date):
        price_obj = SecurityPrice.objects.filter(security_id=security_id, date__lte=date).order_by('-date').first()
        return price_obj.close if price_obj else None

    # Tính equity float
    float_equity = Decimal('0')
    for sec_id, qty in security_quantities.items():
        price = price_map.get(sec_id)
        if price is None:
            price = get_latest_price_before(sec_id, date)
        if price is not None:
            float_equity += qty * price
        else:
            # Nếu vẫn không có giá, log cảnh báo hoặc tùy xử lý
            print(f"[WARN] Missing price for security {sec_id} on or before {date}")
    # Cập nhật lại hoặc trả về equity
    # Giả sử AccountBalance có trường equity
    balance_obj, created = AccountBalance.objects.get_or_create(account=account, date=date)
    balance_obj.float  = float_equity 
    balance_obj.save()

    return float_equity 