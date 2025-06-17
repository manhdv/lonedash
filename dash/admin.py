from django.contrib import admin
from .models import (Indicator, 
                     EconomicData, 
                     Account, 
                     Transaction,
                     AccountBalance, 
                     Security, 
                     SecurityPrice, 
                     TradeExit, 
                     TradeEntry, 
                     PortfolioPerformance, 
                     Language,
                     Currency,
                     Country,
                     UserPreference,
                     UserAPIKey)
# Register your models here.

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
    list_display = ('date', 'type', 'amount', 'account', 'user')
    list_filter = ('type', 'date')
    search_fields = ('description', 'account__name', 'user__username')
    ordering = ('-date',)

@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    list_display = ('account', 'date', 'balance', 'equity', 'float', 'principal')
    list_filter = ('account', 'date')
    search_fields = ('account__name',)
    ordering = ('-date',)

@admin.register(Security)
class SecurityAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'exchange', 'user')
    search_fields = ('code', 'name', 'exchange')
    list_filter = ('exchange', 'api_source')
    ordering = ('-code',)

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
    list_display = ('user', 'date', 'balance', 'equity', 'principal', 'fee', 'tax', 'profit')
    list_filter = ('user', 'date')
    search_fields = ('user__username',)

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol')
    search_fields = ('code', 'name')


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('iso_code', 'name')
    search_fields = ('iso_code', 'name')


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'currency', 'theme')
    autocomplete_fields = ('user', 'language', 'currency')
    search_fields = ('user__username',)

@admin.register(UserAPIKey)
class UserAPIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key_eodhd', 'key_finhub', 'key_alpha_vantage', 'key_yahoo')
    search_fields = ('user__username',)