from django.contrib import admin
from .models import Currency, ExchangeRate

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'is_base')
    search_fields = ('code', 'name')

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('currency', 'rate', 'date')
    list_filter = ('currency', 'date')
    ordering = ('-date',)