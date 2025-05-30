from django.db import models
from django.contrib.auth.models import User
from datetime import date

# Create your models here.
class Setting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Tham chiếu đến User

    finhub_api_key = models.CharField(max_length=255, blank=True, null=True)
    alpha_vantage_api_key = models.CharField(max_length=255, blank=True, null=True)
    eodhd_api_key = models.CharField(max_length=255, blank=True, null=True)
    yahoo_finance_api_key = models.CharField(max_length=255, blank=True, null=True)
    google_map_api_key = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Country(models.Model):
    iso_code = models.CharField(max_length=3, unique=True)  # e.g. 'US', 'VN'
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=10, default='USD')

    def __str__(self):
        return self.name

class Indicator(models.Model):
    code = models.CharField(max_length=50, unique=True)  # e.g. 'gdp', 'inflation'
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, blank=True)  # e.g. '%', 'USD', 'points'
    frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ])

    def __str__(self):
        return self.name

class EconomicData(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE)
    date = models.DateField()
    value = models.DecimalField(max_digits=20, decimal_places=4)

    class Meta:
        unique_together = ('country', 'indicator', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.country} - {self.indicator} @ {self.date}: {self.value}'

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=[
        ('deposit', 'Deposit'),
        ('security', 'Security'),
    ])
    balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='USD')
    date = models.DateField(default=date.today)
    active = models.BooleanField(default=True)

    # metadata
    description = models.TextField(blank=True)
    def __str__(self):
        return f"{self.name} - {self.currency}"

class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transaction')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaction')
    type = models.CharField(max_length=20, choices=[
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('dividien', 'Dividien'),
        ('interest', 'Interest'),
        ('fee', 'Fee'),
    ])
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    currency = models.CharField(max_length=50, default='USD')
    date = models.DateField(default=date.today)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.type} - {self.amount}"

class Security(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security')
    code = models.CharField(max_length=10)
    exchange = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, blank=True)  
    country = models.CharField(max_length=50, default='US')
    currency = models.CharField(max_length=50, default='USD')
    isin = models.CharField(max_length=20, blank=True)
    close = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)

    # metadata
    industry = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'code'], name='unique_user_code')
        ]
        indexes = [
            models.Index(fields=['user', 'code']),
        ]
    def __str__(self):
        return f"{self.code} - {self.name}"


class SecurityPrice(models.Model):
    security = models.ForeignKey(Security, on_delete=models.CASCADE, default=1)
    date = models.DateField(default=date.today)
    open = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    high = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    low = models.DecimalField(max_digits=16, decimal_places=2,default=0)
    close = models.DecimalField(max_digits=16, decimal_places=2)
    adjusted_close = models.DecimalField(max_digits=16, decimal_places=2,default=0)
    volume = models.BigIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['security', 'date'], name='unique_security_date')
        ]
    def __str__(self):
        return f"{self.security.code} - {self.date} - {self.close}"