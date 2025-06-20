from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
from functools import reduce
from operator import mul

import requests

from django.utils import timezone
from django.db.models import Max
from django.contrib.auth.models import User

from .models import (
    Security,
    AccountBalance,
    PortfolioPerformance,
    TradeEntry,
    TradeExit,
    SecurityPrice,
    Transaction,
    Account,
    UserAPIKey,
    UserPreference,
    DailyHoldingEquity,
)


def utils_update_account(account, start_date=None):
    """
    Re-compute balance / fee / tax / principal *and* equity‐float for `account`
    starting from `start_date`.

    If `start_date` is None, the function resumes from the most-recent
    AccountBalance date stored for that account (or today if none exists).
    """

    # 1️⃣ Xác định ngày bắt đầu
    if start_date is None:
        last_bal = (
            AccountBalance.objects.filter(account=account)
            .order_by("-date")
            .first()
        )
        start_date = last_bal.date if last_bal else date.today()

    # 🧹 Xoá dữ liệu cũ từ start_date trở đi
    AccountBalance.objects.filter(account=account, date__gte=start_date).delete()

    # 2️⃣ Lấy balance trước đó (nếu có)
    prev_bal = (
        AccountBalance.objects.filter(account=account, date__lt=start_date)
        .order_by("-date")
        .first()
    )
    balance = prev_bal.balance if prev_bal else Decimal("0")
    fee = prev_bal.fee if prev_bal else Decimal("0")
    tax = prev_bal.tax if prev_bal else Decimal("0")
    principal = prev_bal.principal if prev_bal else Decimal("0")

    # 3️⃣ Lấy giao dịch, entries, exits
    transactions = account.transactions.filter(date__gte=start_date).order_by("date")
    entries = account.entries.filter(date__gte=start_date).order_by("date")
    exits = TradeExit.objects.filter(entry__account=account, date__gte=start_date).order_by("date")

    # 4️⃣ Gom dữ liệu theo ngày
    daily_changes = defaultdict(lambda: Decimal("0"))
    daily_fee = defaultdict(lambda: Decimal("0"))
    daily_tax = defaultdict(lambda: Decimal("0"))
    daily_principal = defaultdict(lambda: Decimal("0"))

    for tx in transactions:
        daily_changes[tx.date] += tx.net_amount
        daily_fee[tx.date] += tx.fee
        daily_tax[tx.date] += tx.tax
        if tx.type in ("deposit", "withdrawal"):
            daily_principal[tx.date] += tx.net_amount

    for entry in entries:
        daily_changes[entry.date] -= entry.net_amount
        daily_fee[entry.date] += entry.fee
        daily_tax[entry.date] += entry.tax

    for ex in exits:
        daily_changes[ex.date] += ex.net_amount
        daily_fee[ex.date] += ex.fee
        daily_tax[ex.date] += ex.tax

    # 5️⃣ Duyệt từng ngày và cập nhật balance + equity
    all_dates = set(daily_changes.keys()) | set(daily_principal.keys())
    if not all_dates:
        all_dates = {start_date}

    today = date.today()
    current = min(all_dates)
    last = max(today, max(all_dates))

    while current <= last:
        balance += daily_changes[current]
        fee += daily_fee[current]
        tax += daily_tax[current]
        principal += daily_principal[current]

        float_equity = utils_calc_float_equity(account, current)

        AccountBalance.objects.update_or_create(
            account=account,
            date=current,
            defaults={
                "balance": balance,
                "fee": fee,
                "tax": tax,
                "principal": principal,
                "float": float_equity,
            },
        )

        current += timedelta(days=1)



# ---------------------------------------------------------------------- #
#  🔧  HÀM PHỤ: tính equity-float cho một ngày cụ thể
# ---------------------------------------------------------------------- #
def utils_calc_float_equity(account, on_date):
    entries = TradeEntry.objects.filter(account=account)
    holdings = defaultdict(Decimal)

    for entry in entries:
        remain = entry.remaining_quantity_at(until_date=on_date)
        if remain > 0:
            holdings[entry.security_id] += remain

    if not holdings:
        return Decimal("0")

    equity = Decimal("0")
    securities = Security.objects.in_bulk(holdings.keys())  # tránh N+1

    for sec_id, qty in holdings.items():
        security = securities.get(sec_id)
        if not security:
            continue
        price = security.price_on(on_date)
        if price:
            equity += qty * price

    return equity



def utils_fetch_security_prices_eodhd(user, security_code, period_days=90, start_date=None):
    """
    Trả về list dict {'date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume'}
    cho security_code, tối đa 90 ngày gần nhất (free plan), giống utils_fetch_security_prices_yahoo.
    Nếu có start_date thì sẽ lọc lại sau khi fetch.
    """
    user_api, _ = UserAPIKey.objects.get_or_create(user=user)

    key_eodhd = user_api.key_eodhd

    if not key_eodhd:
        print("EODHD API key missing (Setting.key_eodhd).")
        return []

    url = (
        f"https://eodhd.com/api/eod/{security_code}"
        f"?period={period_days}d&api_token={key_eodhd}&fmt=json"
    )

    try:
        r = requests.get(url, timeout=10, verify=False)
        r.raise_for_status()
        raw = r.json()
    except Exception as exc:
        print(f"[EODHD] request failed for {security_code}: {exc}")
        return []

    if not isinstance(raw, list):
        print(f"[EODHD] bad response for {security_code}: {raw}")
        return []

    prices = []
    for row in reversed(raw):  # oldest → newest
        try:
            row_date = date.fromisoformat(row["date"])
            if start_date and row_date < start_date:
                continue  # bỏ dữ liệu quá cũ
            prices.append({
                "date": row_date,
                "open": Decimal(str(row["open"])),
                "high": Decimal(str(row["high"])),
                "low": Decimal(str(row["low"])),
                "close": Decimal(str(row["close"])),
                "adjusted_close": Decimal(str(row.get("adjusted_close", row["close"]))),
                "volume": int(row["volume"]),
            })
        except (KeyError, ValueError) as exc:
            print(f"[EODHD] parse error {security_code} {row}: {exc}")

    return prices


def utils_fetch_security_prices_yahoo(security_code, period_days=90, start_date=None):
    # Xác định range param cho yahoo API
    # Nếu start_date có, tính từ đó đến hôm nay, else 3 tháng
    end_date = timezone.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=period_days)
    
    delta_days = (end_date - start_date).days
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{security_code}?range={delta_days}d&interval=1d"
    try:
        r = requests.get(url, headers=headers, verify=False, timeout = 10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Yahoo fetch error for {security_code}: {e}")
        return []

    try:
        timestamps = data['chart']['result'][0]['timestamp']
        indicators = data['chart']['result'][0]['indicators']['quote'][0]
    except (KeyError, IndexError):
        return []

    prices = []
    for i, ts in enumerate(timestamps):
        dt = date.fromtimestamp(ts)
        prices.append({
            'date': dt,
            'open': indicators['open'][i] or 0,
            'high': indicators['high'][i] or 0,
            'low': indicators['low'][i] or 0,
            'close': indicators['close'][i] or 0,
            'volume': indicators['volume'][i] or 0,
            'adjusted_close': indicators.get('adjclose', [0]*len(timestamps))[i] or 0
        })
    return prices


def utils_update_security_prices_for_user(user):
    securities = Security.objects.filter(user=user)
    for security in securities:
        latest_price = SecurityPrice.objects.filter(security=security).order_by('-date').first()
        if latest_price:
            start_date = latest_price.date + timedelta(days=1)
        else:
            start_date = timezone.now().date() - timedelta(days=90)
        print("start date = " + str(start_date))
        if start_date > timezone.now().date():
            continue

        if security.api_source == 'eodhd':
            symbol = f"{security.code}.{security.exchange}"
            prices = utils_fetch_security_prices_eodhd(user, symbol, start_date=start_date)
            if not prices:
                continue

            for p in prices:
                SecurityPrice.objects.update_or_create(
                    security=security,
                    date=p['date'],
                    defaults={
                        'open': p['open'],
                        'high': p['high'],
                        'low': p['low'],
                        'close': p['close'],
                        'adjusted_close': p['adjusted_close'],
                        'volume': p['volume'],
                    }
                )
            print(f"Updated prices from EODHD for {security.code} from {start_date} to {timezone.now().date()}")
            continue


        elif security.api_source == 'yahoo' or not security.api_source:
            prices = utils_fetch_security_prices_yahoo(security.code, start_date=start_date)
            if not prices:
                continue

            for p in prices:
                SecurityPrice.objects.update_or_create(
                    security=security,
                    date=p['date'],
                    defaults={
                        'open': p['open'],
                        'high': p['high'],
                        'low': p['low'],
                        'close': p['close'],
                        'adjusted_close': p['adjusted_close'],
                        'volume': p['volume'],
                    }
                )
            print(f"Updated prices for {security.code} from {start_date} to {timezone.now().date()}")
        else:
            print(f"Unknown api_source '{security.api_source}' for {security.code}, skipping.")

# ---- helper -------------------------------------------------------------
def utils_format_currency_pair(source: str, target: str) -> str:
    source = source.upper()
    target = target.upper()
    return f"{target}=X" if source == "USD" else f"{source}{target}=X"



def utils_convert_currency(source: str, target: str, as_of: date) -> Decimal:
    source = source.upper()
    target = target.upper()

    if source == target:
        return Decimal("1")

    if target == "USD":
        reverse_symbol = utils_format_currency_pair("USD", source)
        security = Security.objects.filter(code=reverse_symbol).first()
        if security:
            quote = security.price_on(as_of)
            if quote and quote != 0:
                return Decimal("1") / quote
            print(f"[DEBUG] No price found for {reverse_symbol} at {as_of}")
        else:
            print(f"[DEBUG] reverse_symbol {reverse_symbol} does not exist")

    symbol = utils_format_currency_pair(source, target)
    security = Security.objects.filter(code=symbol).first()
    if not security:
        return Decimal("1")

    quote = security.price_on(as_of)
    return quote if quote else Decimal("1")


def utils_recalc_portfolio(user, day):
    """Aggregate all account balances for `user` on `day` → USD totals."""
    try:
        target_currency = UserPreference.objects.get(user=user).currency.code
    except UserPreference.DoesNotExist:
        # fallback nếu user chưa có thiết lập
        target_currency = "USD"
    print(f"[INFO] target currency {target_currency}") 
    
    # Kiểm tra nếu balance của mỗi account chưa được update đến ngày `day`, thì gọi update
    accounts = Account.objects.filter(user=user)
    for account in accounts:
        latest_balance = (
            AccountBalance.objects
            .filter(account=account)
            .aggregate(latest=Max('date'))['latest']
        )
        if latest_balance is None or latest_balance < day:
            utils_update_account(account)


    qs = (
        AccountBalance.objects
        .select_related('account')
        .filter(account__user=user, date=day)
    )

    totals = {
        'principal': Decimal('0'),
        'balance'  : Decimal('0'),
        'float'    : Decimal('0'),
        'fee'      : Decimal('0'),
        'tax'      : Decimal('0'),
    }

    for bal in qs:
        print(f"[INFO] Account Balance currency {bal.account.currency.code}")
        fx = utils_convert_currency(bal.account.currency.code, target_currency, bal.date)
        print (f"convert fx = {fx}")
        totals['principal'] += (bal.principal or 0) * fx
        totals['balance']   += (bal.balance   or 0) * fx
        totals['float']     += (bal.float     or 0) * fx
        totals['fee']       += (bal.fee       or 0) * fx
        totals['tax']       += (bal.tax       or 0) * fx

    # Tính transaction trong ngày đó
    txs = Transaction.objects.filter(account__user=user, date=day)
    total_tx = Decimal('0')
    for tx in txs:
        fx = utils_convert_currency(tx.account.currency.code, target_currency, tx.date)
        total_tx += tx.net_amount * fx

    totals['transaction'] = total_tx

    PortfolioPerformance.objects.update_or_create(
        user=user,
        date=day,
        defaults=totals,
    )


def utils_recalc_from(user, start_date):
    today = timezone.now().date()
    current = start_date
    while current <= today:
        print(f"↻ Recalculating portfolio for {user.username} on {current}")
        utils_recalc_portfolio(user, current)
        current += timedelta(days=1)

def utils_calculate_drawdown(entries):  # entries: list of PortfolioPerformance ordered by date
    peak = Decimal('1.0')
    nav = Decimal('1.0')
    max_drawdown = Decimal('0.0')

    for i in range(1, len(entries)):
        prev = entries[i - 1]
        curr = entries[i]

        if prev.equity == 0 or curr.equity == 0:
            continue

        if curr.transaction == 0:
            daily_return = curr.equity / prev.equity
            nav *= daily_return
            peak = max(peak, nav)
            dd = (nav - peak) / peak
            max_drawdown = min(max_drawdown, dd)

        else:
            # Skip or reset nav to current if you want
            nav = nav  # or nav = nav (keep) or nav = 1 (reset)
            peak = max(peak, nav)

    return float(max_drawdown * 100)


from decimal import Decimal
from functools import reduce
from operator import mul

def utils_calculate_twrr(entries):
    """
    entries: list of PortfolioPerformance, sorted by date ascending
    """
    if not entries:
        print("No entries.")
        return Decimal(0)

    twrr_factors = []
    start_equity = None

    for i, entry in enumerate(entries):
        equity = entry.equity
        tx = entry.transaction

        print(f"[{entry.date}] Equity: {equity}, Tx: {tx}")

        if start_equity is None:
            start_equity = equity
            print(f"  Start equity initialized to {start_equity}")
            continue

        if tx != 0:
            if start_equity == 0:
                r = 0
                print(f"  Division by zero avoided (start_equity == 0), r = 0")
            else:
                r = (equity - start_equity - tx) / start_equity
                print(f"  Tx detected → r = ({equity} - {start_equity} - {tx}) / {start_equity} = {r}")
            twrr_factors.append(Decimal(1) + Decimal(r))
            print(f"  Added factor: {Decimal(1) + Decimal(r)}")
            start_equity = equity
            print(f"  Reset start equity to {start_equity}")

    # Handle final period (no tx at end but still value change)
    entries = list(entries)
    last_equity = entries[-1].equity
    if start_equity != last_equity:
        if start_equity == 0:
            r = 0
            print(f"[FINAL] Avoided division by zero")
        else:
            r = (last_equity - start_equity) / start_equity
            print(f"[FINAL] r = ({last_equity} - {start_equity}) / {start_equity} = {r}")
        twrr_factors.append(Decimal(1) + Decimal(r))
        print(f"[FINAL] Added last factor: {Decimal(1) + Decimal(r)}")

    if not twrr_factors:
        print("No factors to multiply.")
        return Decimal(0)

    product = reduce(mul, twrr_factors, Decimal(1))
    twrr = (product - Decimal(1)) * 100
    print(f"TWRR factors: {twrr_factors}")
    print(f"TWRR product: {product}")
    print(f"TWRR result: {twrr}")

    return twrr

def utils_recalc_daily_holdings(user: User, security: Security, from_date: date):

    DailyHoldingEquity.objects.filter(
        user=user,
        security=security,
        date__gte=from_date
    ).delete()

    today = date.today()
    current_date = from_date

    while current_date <= today:
        qty = 0
        entries = TradeEntry.objects.filter(
            account__user=user,
            security=security,
            date__lte=current_date
        )
        for entry in entries:
            qty += entry.remaining_quantity_at(current_date)

        if qty == 0:
            current_date += timedelta(days=1)
            continue

        price = security.price_on(current_date)
        if not price:
            current_date += timedelta(days=1)
            continue

        equity = qty * price
        currency = entries.first().account.currency.code if entries else "USD"

        DailyHoldingEquity.objects.create(
            user=user,
            security=security,
            date=current_date,
            equity=equity,
            currency=currency
        )

        current_date += timedelta(days=1)
