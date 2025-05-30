from django.contrib import admin
from .models import Country, Indicator, EconomicData, Account, Transaction
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