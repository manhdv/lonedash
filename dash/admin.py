from django.contrib import admin
from .models import Country, Indicator, EconomicData, Account, Transaction, AccountBalance, Setting, Security, SecurityPrice
# Register your models here.

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_code')
    search_fields = ('name', 'iso_code')

@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'unit', 'frequency')
    search_fields = ('name', 'code')
    list_filter = ('frequency',)

@admin.register(EconomicData)
class EconomicDataAdmin(admin.ModelAdmin):
    list_display = ('country', 'indicator', 'date', 'value')
    list_filter = ('country', 'indicator')
    date_hierarchy = 'date'
    search_fields = ('country__name', 'indicator__name')

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'currency', 'active')
    list_filter = ('type', 'currency', 'active')
    search_fields = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'type', 'amount', 'currency', 'account', 'user')
    list_filter = ('type', 'date', 'currency')
    search_fields = ('description', 'account__name', 'user__username')
    ordering = ('-date',)

@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    list_display = ('account', 'date', 'balance')
    list_filter = ('account', 'date')
    search_fields = ('account__name',)
    ordering = ('-date',)

@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'key_finhub', 'key_alpha_vantage', 'key_eodhd', 'key_yahoo', 'key_google_map')

@admin.register(Security)
class SecurityAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'exchange', 'country', 'user', 'date')
    search_fields = ('code', 'name', 'exchange')
    list_filter = ('exchange', 'country', 'api_source')
    ordering = ('-date',)

@admin.register(SecurityPrice)
class SecurityPriceAdmin(admin.ModelAdmin):
    list_display = ('security', 'date', 'close', 'volume')
    list_filter = ('security', 'date')
    search_fields = ('security__code',)