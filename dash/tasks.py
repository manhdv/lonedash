import requests
from datetime import date, timedelta
from django.utils import timezone
from django.db import transaction
from dash.models import Security, SecurityPrice, Setting

def fetch_security_prices_yahoo(security_code, period_days=90, start_date=None):
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


def update_security_prices_for_user(user):
    securities = Security.objects.filter(user=user)
    for security in securities:
        latest_price = SecurityPrice.objects.filter(security=security).order_by('-date').first()
        if latest_price:
            start_date = latest_price.date + timedelta(days=1)
        else:
            start_date = timezone.now().date() - timedelta(days=90)

        if start_date > timezone.now().date():
            continue

        if security.api_source == 'eodhd':
            # TODO: call eodhd fetch function ở đây
            print(f"Fetching from EODHD for {security.code} - NOT IMPLEMENTED")
            continue
        elif security.api_source == 'yahoo' or not security.api_source:
            prices = fetch_security_prices_yahoo(security.code, start_date=start_date)
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

