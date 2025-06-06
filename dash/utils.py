from datetime import timedelta, date as dt_date
from decimal import Decimal
from collections import defaultdict

from .models import (
    AccountBalance,
    TradeExit,
    TradeEntry,
    SecurityPrice,
)

def update_account(account, start_date=None):
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
        start_date = last_bal.date if last_bal else dt_date.today()

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
        account.transaction.filter(date__gte=start_date).order_by("date")
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
        daily_changes[tx.date] += tx.net_amount()
        daily_fee[tx.date] += tx.fee
        daily_tax[tx.date] += tx.tax
        if tx.type == "deposit":
            daily_principal[tx.date] += tx.net_amount()
        elif tx.type == "withdraw":
            daily_principal[tx.date] -= tx.net_amount()

    for entry in entries:
        net = entry.quantity * entry.price + entry.fee + entry.tax
        daily_changes[entry.date] -= net
        daily_fee[entry.date] += entry.fee
        daily_tax[entry.date] += entry.tax


    for ex in exits:
        gross = ex.quantity * ex.price
        net = gross - ex.fee - ex.tax
        daily_changes[ex.date] += net
        daily_fee[ex.date] += ex.fee
        daily_tax[ex.date] += ex.tax

    all_dates = (
        set(daily_changes.keys()) | set(daily_principal.keys()) or {start_date}
    )
    today = dt_date.today()
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
        float_equity = _calc_float_equity(account, current)

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
def _calc_float_equity(account, on_date):
    entries = TradeEntry.objects.filter(account=account)
    holdings = defaultdict(Decimal)

    for entry in entries:
        remain = entry.remaining_quantity(until_date=on_date)
        if remain > 0:
            holdings[entry.security_id] += remain

    if not holdings:
        return Decimal("0")

    prices = SecurityPrice.objects.filter(
        security_id__in=holdings.keys(), date=on_date
    )
    price_map = {p.security_id: p.close for p in prices}

    def latest_before(sec_id):
        obj = (
            SecurityPrice.objects.filter(
                security_id=sec_id, date__lte=on_date
            )
            .order_by("-date")
            .first()
        )
        return obj.close if obj else None

    equity = Decimal("0")
    for sec_id, qty in holdings.items():
        price = price_map.get(sec_id) or latest_before(sec_id)
        if price:
            equity += qty * price
    return equity
