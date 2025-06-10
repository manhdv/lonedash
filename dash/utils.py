from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict

import requests

from django.utils import timezone
from django.db.models import Max

from dash.models import Security, SecurityPrice, Setting
from .models import (
    AccountBalance,
    PortfolioPerformance,
    TradeEntry,
    TradeExit,
    SecurityPrice,
    Transaction,
    Account
)


def utils_update_account(account, start_date=None):
    """
    Re-compute balance / fee / tax / principal *and* equity‐float for `account`
    starting from `start_date`.

    If `start_date` is None, the function resumes from the most-recent
    AccountBalance date stored for that account (or today if none exists).
    """
    # 1️⃣  Xác định ngày bắt đầu
    if start_date is None:
        last_bal = (
            AccountBalance.objects.filter(account=account)
            .order_by("-date")
            .first()
        )
        start_date = last_bal.date if last_bal else date.today()

    # ------------------------------------------------------------------ #
    # 2️⃣  CẬP NHẬT balance / fee / tax / principal  (giống hàm cũ)
    # ------------------------------------------------------------------ #
    prev_bal = (
        AccountBalance.objects.filter(account=account, date__lt=start_date)
        .order_by("-date")
        .first()
    )
    balance = prev_bal.balance if prev_bal else Decimal("0")
    fee = prev_bal.fee if prev_bal else Decimal("0")
    tax = prev_bal.tax if prev_bal else Decimal("0")
    principal = prev_bal.principal if prev_bal else Decimal("0")

    transactions = (
        account.transactions.filter(date__gte=start_date).order_by("date")
    )
    entries = account.entries.filter(date__gte=start_date).order_by("date")
    exits = (
        TradeExit.objects.filter(entry__account=account, date__gte=start_date)
        .order_by("date")
    )

    daily_changes = defaultdict(Decimal)
    daily_fee = defaultdict(Decimal)
    daily_tax = defaultdict(Decimal)
    daily_principal = defaultdict(Decimal)

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

    all_dates = (
        set(daily_changes.keys()) | set(daily_principal.keys()) or {start_date}
    )
    today = date.today()
    current = min(all_dates)
    last = max(today, max(all_dates))

    while current <= last:
        balance += daily_changes[current]
        fee += daily_fee[current]
        tax += daily_tax[current]
        principal += daily_principal[current]

        # ------------------------------------------------------------------ #
        # 3️⃣  TÍNH equity-float cho current
        # ------------------------------------------------------------------ #
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
    fallback_price = {}  # entry fallback price by security

    for entry in entries:
        remain = entry.remaining_quantity_at(until_date=on_date)
        if remain > 0:
            holdings[entry.security_id] += remain
            # Ghi nhận giá entry mới nhất làm fallback
            if (
                entry.security_id not in fallback_price
                or entry.date > fallback_price[entry.security_id][0]
            ):
                fallback_price[entry.security_id] = (entry.date, entry.price)

    if not holdings:
        return Decimal("0")

    prices = SecurityPrice.objects.filter(
        security_id__in=holdings.keys(), date=on_date
    )
    price_map = {p.security_id: p.close for p in prices}

    def latest_before(sec_id):
        obj = (
            SecurityPrice.objects.filter(
                security_id=sec_id,
                date__lt=on_date,
                close__gt=0
            )
            .order_by("-date")
            .first()
        )
        return obj.close if obj else None

    equity = Decimal("0")
    for sec_id, qty in holdings.items():
        price_today = price_map.get(sec_id)
        price = (
            price_today if price_today and price_today > 0
            else latest_before(sec_id)
            or fallback_price.get(sec_id, (None, None))[1]  # dùng entry.price
        )
        if price:
            equity += qty * price

    return equity






def utils_fetch_security_prices_eodhd(security_code, period_days=90, start_date=None):
    """
    Trả về list dict {'date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume'}
    cho security_code, tối đa 90 ngày gần nhất (free plan), giống utils_fetch_security_prices_yahoo.
    Nếu có start_date thì sẽ lọc lại sau khi fetch.
    """
    api_key = Setting.objects.values_list("key_eodhd", flat=True).first() or ""
    if not api_key:
        print("EODHD API key missing (Setting.key_eodhd).")
        return []

    url = (
        f"https://eodhd.com/api/eod/{security_code}"
        f"?period={period_days}d&api_token={api_key}&fmt=json"
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
            prices = utils_fetch_security_prices_eodhd(symbol, start_date=start_date)
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




def utils_fx_to_usd(currency: str, as_of: date) -> Decimal:
    # USD thì khỏi tra cứu
    if currency.upper() == "USD":
        return Decimal("1")

    symbol = f"{currency.upper()}=X"
    if not Security.objects.filter(code=symbol).exists():
        # Không có mã FX này → coi như 1:1
        return Decimal("1")

    # 1) Tìm giá gần nhất về quá khứ (<= as_of)
    quote = (
        SecurityPrice.objects
        .filter(
            security__code=symbol,
            date__lte=as_of,
            close__gt=0
        )
        .order_by('-date')
        .first()
    )

    if quote is None:
        # 2) Không có quá khứ → lấy giá sớm nhất sau as_of
        quote = (
            SecurityPrice.objects
            .filter(
                security__code=symbol,
                date__gt=as_of,
                close__gt=0
            )
            .order_by('date')
            .first()
        )

    if quote is None:
        # 3) Bó tay, fallback 1:1
        return Decimal("1")

    # USD per 1 unit currency
    return Decimal("1") / quote.close



def utils_recalc_portfolio(user, day):
    """Aggregate all account balances for `user` on `day` → USD totals."""

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
        fx = utils_fx_to_usd(bal.account.currency.code, bal.date)
        totals['principal'] += (bal.principal or 0) * fx
        totals['balance']   += (bal.balance   or 0) * fx
        totals['float']     += (bal.float     or 0) * fx
        totals['fee']       += (bal.fee       or 0) * fx
        totals['tax']       += (bal.tax       or 0) * fx

    # Tính transaction trong ngày đó
    txs = Transaction.objects.filter(account__user=user, date=day)
    total_tx = Decimal('0')
    for tx in txs:
        fx = utils_fx_to_usd(tx.account.currency.code, tx.date)
        total_tx += tx.net_amount * fx

    totals['transaction'] = total_tx

    PortfolioPerformance.objects.update_or_create(
        user=user,
        date=day,
        defaults=totals,
    )


def utils_calculate_max_drawdown(data):
    max_nav = Decimal('0')
    max_dd = Decimal('0')

    for p in data:
        if p.principal > 0:
            nav = p.equity / p.principal
        else:
            nav = Decimal('1')  # hoặc continue nếu muốn bỏ qua ngày không đầu tư

        if nav > max_nav:
            max_nav = nav
        dd = (max_nav - nav) / max_nav if max_nav > 0 else 0
        if dd > max_dd:
            max_dd = dd

    return round(max_dd * 100, 2)
