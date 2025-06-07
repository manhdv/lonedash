from django.contrib import admin
from .models import Country, Indicator, EconomicData, Account, Transaction, AccountBalance, Setting, Security, SecurityPrice, TradeExit, TradeEntry, PortfolioPerformance
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
    list_display = ('account', 'date', 'balance', 'equity', 'float')
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

class TradeExitInline(admin.TabularInline):
    model = TradeExit
    extra = 0

@admin.register(TradeEntry)
class TradeEntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'account', 'security', 'quantity', 'price', 'fee', 'tax', 'is_closed')
    list_filter = ('account', 'security', 'date')
    search_fields = ('security__code', 'account__name')
    inlines = [TradeExitInline]

@admin.register(TradeExit)
class TradeExitAdmin(admin.ModelAdmin):
    list_display = ('date', 'entry', 'price', 'quantity', 'fee', 'tax', 'profit')
    list_filter = ('date',)

@admin.register(PortfolioPerformance)
class PortfolioPerformanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'balance', 'float', 'principal', 'fee', 'tax', 'profit', 'profit_percent')
    list_filter = ('user', 'date')
    search_fields = ('user__username',)