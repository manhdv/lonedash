from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.core.exceptions import ValidationError

# Create your models here.
class Setting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Tham chiếu đến User

    key_finhub= models.CharField(max_length=255, blank=True, null=True)
    key_alpha_vantage = models.CharField(max_length=255, blank=True, null=True)
    key_eodhd = models.CharField(max_length=255, blank=True, null=True)
    key_yahoo = models.CharField(max_length=255, blank=True, null=True)
    key_google_map = models.CharField(max_length=255, blank=True, null=True)

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
    value = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        unique_together = ('country', 'indicator', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.country} - {self.indicator} @ {self.date}: {self.value}'

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=[
        ('deposit', 'Deposit'),
        ('broker', 'Broker'),
    ])
    currency = models.CharField(max_length=10, default='USD')
    active = models.BooleanField(default=True)

    # metadata
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.currency}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class AccountBalance(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='balances')
    date = models.DateField(default=date.today)
    principal = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    float = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    class Meta:
        unique_together = ('account', 'date')  # 1 balance / day
    
    @property
    def equity(self):
        return self.balance + self.float
    
    def __str__(self):
        return f"{self.account.name} - {self.date}: {self.balance}"


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transaction')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaction')
    type = models.CharField(max_length=20, choices=[
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('dividien', 'Dividien'),
        ('interest', 'Interest'),
        ('fee', 'Fee')
    ])
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    currency = models.CharField(max_length=50, default='USD')
    date = models.DateField(default=date.today)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def net_amount(self):
        money_in = ['deposit', 'transfer_in', 'dividien', 'interest']
        money_out = ['withdrawal', 'transfer_out', 'fee']

        if self.type in money_in:
            return self.amount - self.fee - self.tax
        elif self.type in money_out:
            return -(self.amount + self.fee + self.tax)
        else:
            return Decimal('0.0')  # hoặc raise nếu có loại lạ

    def __str__(self):
        return f"{self.date} - {self.type} - {self.amount}"

class TradeEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='entries')
    security = models.ForeignKey('Security', on_delete=models.CASCADE, related_name='entries')

    quantity = models.DecimalField(max_digits=16, decimal_places=2)
    price = models.DecimalField(max_digits=16, decimal_places=2)
    fee = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    date = models.DateField(default=date.today)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.date} - BUY {self.quantity} x {self.security.code} @ {self.price}"


    class Meta:
        ordering = ['-date']

    @property
    def gross_amount(self):
        return self.quantity * self.price

    @property
    def net_amount(self):
        return self.gross_amount - self.fee - self.tax
    
    def filled_quantity(self, until_date=None):
        qs = self.exits.all()
        if until_date:
            qs = qs.filter(date__lte=until_date)
        return qs.aggregate(total=models.Sum('quantity'))['total'] or Decimal('0')

    def remaining_quantity(self, until_date=None):
        return self.quantity - self.filled_quantity(until_date)

    @property
    def is_closed(self):
        return self.remaining_quantity == 0
    
    def __str__(self):
        return f"{self.date} - BUY {self.quantity} x {self.security.code} @ {self.price}"
    
class TradeExit(models.Model):
    entry = models.ForeignKey(TradeEntry, on_delete=models.CASCADE, related_name='exits')

    price = models.DecimalField(max_digits=16, decimal_places=2)
    quantity = models.DecimalField(max_digits=16, decimal_places=2)  # Allow partial
    fee = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    date = models.DateField(default=date.today)

    class Meta:
        ordering = ['-date'] 

    def clean(self):
        # Ensure quantity doesn't exceed remaining entry quantity
        if self.quantity > self.entry.remaining_quantity:
            raise ValidationError("Exit quantity cannot exceed remaining entry quantity")
       
    @property
    def profit(self):
        """
        Profit for this exit, accounting for partial quantity:
        (exit_price - entry_price) * quantity - prorated entry costs - exit costs
        """
        gross = (self.price - self.entry.price) * self.quantity
        # Prorate entry fee & tax proportionally to the portion closed
        fraction = self.quantity / self.entry.quantity
        entry_fee_share = self.entry.fee * fraction
        entry_tax_share = self.entry.tax * fraction
        cost = entry_fee_share + entry_tax_share + self.fee + self.tax
        return gross - cost

    def __str__(self):
        return f"{self.date} - SELL {self.quantity} x {self.entry.security.code} @ {self.price}"


class Security(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='country')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security')
    code = models.CharField(max_length=10)
    exchange = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, blank=True)  
    isin = models.CharField(max_length=20, blank=True)
    close = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    date = models.DateField(default=date.today)

    # metadata
    api_source = models.CharField(max_length=50, blank=True, null=True)
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
    security = models.ForeignKey('Security', on_delete=models.CASCADE, default=1)
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
