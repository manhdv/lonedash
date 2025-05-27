import requests
from bs4 import BeautifulSoup
from datetime import date
from dash.models import Country, Indicator, EconomicData
from django.core.management.base import BaseCommand

URL = "https://tradingeconomics.com/matrix"
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}

def scrape_te_matrix():
    r = requests.get(URL, headers=headers, verify=False)
    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.find("table", {"id": "matrix"})
    rows = table.find_all("tr")

    data = []
    header = []

    for i, row in enumerate(rows):
        cols = row.find_all(["th", "td"])
        texts = [col.get_text(strip=True) for col in cols]

        if i == 0:
            header = texts
            continue

        if not texts or len(texts) < 2:
            continue

        country_data = {"country": texts[0]}
        for j in range(1, len(texts)):
            key = header[j] if j < len(header) else f"col_{j}"
            country_data[key] = texts[j]

        data.append(country_data)

    return data



INDICATOR_MAPPING = {
    'GDP': 'gdp',
    'GDP Growth': 'gdp_growth',
    'Interest Rate': 'interest_rate',
    'Inflation Rate': 'inflation_rate',
    'Jobless Rate': 'unemployment_rate',
    'Gov. Budget': 'government_budget',
    'Debt/GDP': 'debt_to_gdp',
    'Current Account': 'current_account',
    'Population': 'population'
}

INDICATOR_META = {
    'gdp': ('GDP', 'USD Bn', 'yearly'),
    'gdp_growth': ('GDP Growth', '%', 'quarterly'),
    'interest_rate': ('Interest Rate', '%', 'monthly'),
    'inflation_rate': ('Inflation Rate', '%', 'monthly'),
    'unemployment_rate': ('Unemployment Rate', '%', 'monthly'),
    'government_budget': ('Government Budget', '% GDP', 'yearly'),
    'debt_to_gdp': ('Debt to GDP', '%', 'yearly'),
    'current_account': ('Current Account', '% GDP', 'yearly'),
    'population': ('Population', 'millions', 'yearly'),
}

# Map title -> indicator.code
def map_matrix_data_to_economic_data(matrix_data: list[dict]):
    today = date.today()

    for row in matrix_data:
        country_name = row.get('country')
        if not country_name:
            continue

        try:
            country_obj = Country.objects.get(name=country_name)
        except Country.DoesNotExist:
            print(f"Country not found: {country_name}")
            continue  # <- don't crash later

        for k, v in row.items():
            if k == 'country' or v in ('', None, 'N/A'):
                continue

            indicator_code = INDICATOR_MAPPING.get(k)
            if not indicator_code:
                continue

            try:
                value = float(v.replace(',', '').replace('%', ''))
            except ValueError:
                continue

            name, unit, freq = INDICATOR_META.get(indicator_code, (k, '', 'yearly'))
            indicator_obj, _ = Indicator.objects.get_or_create(
                code=indicator_code,
                defaults={'name': name, 'unit': unit, 'frequency': freq}
            )

            EconomicData.objects.update_or_create(
                country=country_obj,
                indicator=indicator_obj,
                date=today,
                defaults={'value': value}
            )

class Command(BaseCommand):
    help = "Scrape TradingEconomics matrix and save data to DB"
    matrix_data = scrape_te_matrix()
    for entry in matrix_data[:1]:  # Show first 5 countries
        print(entry)

    map_matrix_data_to_economic_data(matrix_data)
    def handle(self, *args, **options):
        matrix_data = scrape_te_matrix()
        map_matrix_data_to_economic_data(matrix_data)
        self.stdout.write(self.style.SUCCESS("TE matrix scraped and saved."))