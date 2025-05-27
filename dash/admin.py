from django.contrib import admin
from .models import Country, Indicator, EconomicData
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