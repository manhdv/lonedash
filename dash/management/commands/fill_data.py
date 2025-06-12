# myapp/management/commands/fill_data.py

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dash.models import Country, Currency, Language, UserPreference

User = get_user_model()

class Command(BaseCommand):
    help = "Fill initial data for Currency, Language, Country, and create superuser"

    def handle(self, *args, **options):
        self.fill_currencies()
        self.fill_languages()
        self.fill_countries()
        self.create_superuser()
        self.stdout.write(self.style.SUCCESS("✅ All initial data filled successfully."))

    def fill_currencies(self):
        if Currency.objects.exists():
            self.stdout.write("Currency already populated.")
            return
        Currency.objects.bulk_create([
            Currency(code='USD', name='US Dollar', symbol='$'),
            Currency(code='EUR', name='Euro', symbol='€'),
            Currency(code='JPY', name='Japanese Yen', symbol='¥'),
            Currency(code='GBP', name='British Pound', symbol='£'),
            Currency(code='AUD', name='Australian Dollar', symbol='A$'),
            Currency(code='CAD', name='Canadian Dollar', symbol='C$'),
            Currency(code='CHF', name='Swiss Franc', symbol='CHF'),
            Currency(code='CNY', name='Chinese Yuan', symbol='¥'),
            Currency(code='HKD', name='Hong Kong Dollar', symbol='HK$'),
            Currency(code='NZD', name='New Zealand Dollar', symbol='NZ$'),
            Currency(code='SEK', name='Swedish Krona', symbol='kr'),
            Currency(code='KRW', name='South Korean Won', symbol='₩'),
            Currency(code='SGD', name='Singapore Dollar', symbol='S$'),
            Currency(code='NOK', name='Norwegian Krone', symbol='kr'),
            Currency(code='MXN', name='Mexican Peso', symbol='$'),
            Currency(code='INR', name='Indian Rupee', symbol='₹'),
            Currency(code='RUB', name='Russian Ruble', symbol='₽'),
            Currency(code='ZAR', name='South African Rand', symbol='R'),
            Currency(code='TRY', name='Turkish Lira', symbol='₺'),
            Currency(code='BRL', name='Brazilian Real', symbol='R$'),
            Currency(code='TWD', name='New Taiwan Dollar', symbol='NT$'),
            Currency(code='DKK', name='Danish Krone', symbol='kr'),
            Currency(code='PLN', name='Polish Zloty', symbol='zł'),
            Currency(code='THB', name='Thai Baht', symbol='฿'),
            Currency(code='IDR', name='Indonesian Rupiah', symbol='Rp'),
            Currency(code='HUF', name='Hungarian Forint', symbol='Ft'),
            Currency(code='CZK', name='Czech Koruna', symbol='Kč'),
            Currency(code='ILS', name='Israeli New Shekel', symbol='₪'),
            Currency(code='CLP', name='Chilean Peso', symbol='$'),
            Currency(code='PHP', name='Philippine Peso', symbol='₱'),
            Currency(code='AED', name='UAE Dirham', symbol='د.إ'),
            Currency(code='COP', name='Colombian Peso', symbol='$'),
            Currency(code='SAR', name='Saudi Riyal', symbol='﷼'),
            Currency(code='MYR', name='Malaysian Ringgit', symbol='RM'),
            Currency(code='RON', name='Romanian Leu', symbol='lei'),
            Currency(code='VND', name='Vietnamese Dong', symbol='₫'),
            Currency(code='EGP', name='Egyptian Pound', symbol='£'),
            Currency(code='PKR', name='Pakistani Rupee', symbol='₨'),
            Currency(code='NGN', name='Nigerian Naira', symbol='₦'),
            Currency(code='BDT', name='Bangladeshi Taka', symbol='৳'),
            Currency(code='KZT', name='Kazakhstani Tenge', symbol='₸'),
            Currency(code='UAH', name='Ukrainian Hryvnia', symbol='₴'),
            Currency(code='LKR', name='Sri Lankan Rupee', symbol='Rs'),
            Currency(code='KES', name='Kenyan Shilling', symbol='KSh'),
            Currency(code='MAD', name='Moroccan Dirham', symbol='د.م.'),
            Currency(code='DZD', name='Algerian Dinar', symbol='دج'),
            Currency(code='PEN', name='Peruvian Sol', symbol='S/'),
            Currency(code='ARS', name='Argentine Peso', symbol='$'),
            Currency(code='IQD', name='Iraqi Dinar', symbol='ع.د'),
        ])
        self.stdout.write("✔ Currencies added.")

    def fill_languages(self):
        if Language.objects.exists():
            self.stdout.write("Language already populated.")
            return
        Language.objects.bulk_create([
            Language(code='en', name='English'),
            Language(code='vi', name='Vietnamese'),
            Language(code='fr', name='French'),
            Language(code='es', name='Spanish'),
            Language(code='de', name='German'),
            Language(code='zh', name='Chinese'),
            Language(code='ja', name='Japanese'),
            Language(code='ko', name='Korean'),
        ])
        self.stdout.write("✔ Languages added.")

    def fill_countries(self):
        if Country.objects.exists():
            self.stdout.write("Country already populated.")
            return
        Country.objects.bulk_create([
            Country(iso_code='US', name='United States'),
            Country(iso_code='VN', name='Vietnam'),
            Country(iso_code='JP', name='Japan'),
            Country(iso_code='FR', name='France'),
            Country(iso_code='DE', name='Germany'),
            Country(iso_code='CN', name='China'),
        ])
        self.stdout.write("✔ Countries added.")

    def fill_userpref_for_user(self, user):
        if UserPreference.objects.filter(user=user).exists():
            self.stdout.write(f"UserPreference already exists for '{user.username}'.")
            return

        language, _ = Language.objects.get_or_create(code='en', defaults={'name': 'English'})
        currency, _ = Currency.objects.get_or_create(code='USD', defaults={'name': 'US Dollar', 'symbol': '$'})

        UserPreference.objects.create(
            user=user,
            language=language,
            currency=currency,
            theme='light'
        )
        self.stdout.write(f"✔ UserPreference created for '{user.username}'.")


    def create_superuser(self):
        username = os.getenv("SUPERUSER_NAME", "admin")
        email = os.getenv("SUPERUSER_EMAIL", "admin@example.com")
        password = os.getenv("SUPERUSER_PASSWORD", "admin")

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(f"✔ Superuser '{username}' created.")
        else:
            user = User.objects.get(username=username)
            self.stdout.write(f"Superuser '{username}' already exists.")

        # Gọi fill_userpref cho user này
        self.fill_userpref_for_user(user)