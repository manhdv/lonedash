from django.core.management.base import BaseCommand
from dash.models import Indicator

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

class Command(BaseCommand):
    help = 'Fill Indicator table with default data'

    def handle(self, *args, **options):
        for _, code in INDICATOR_MAPPING.items():
            name, unit, freq = INDICATOR_META.get(code, ('Unknown', '', 'yearly'))
            obj, created = Indicator.objects.get_or_create(
                code=code,
                defaults={'name': name, 'unit': unit, 'frequency': freq}
            )
            if not created:
                obj.name = name
                obj.unit = unit
                obj.frequency = freq
                obj.save()

        self.stdout.write(self.style.SUCCESS('Indicators filled/updated successfully.'))
