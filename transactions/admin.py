from django.contrib import admin
from .models import Distribution, PurchaseTransaction, DrawdownReceipt, CapitalCall

@admin.register(Distribution)
class DistributionAdmin(admin.ModelAdmin):
    # distribution_date instead of paid_date
    list_display = ('fund', 'investor', 'distribution_type', 'gross_amount', 'distribution_date')

@admin.register(PurchaseTransaction)
class PurchaseAdmin(admin.ModelAdmin):
    # price_per_share and transaction_date instead of price/trade_date
    list_display = ('fund', 'investee_company', 'quantity', 'price_per_share', 'transaction_date')

@admin.register(DrawdownReceipt)
class ReceiptAdmin(admin.ModelAdmin):
    # Using methods to pull fund/investor from the linked CapitalCall
    list_display = ('transaction_ref', 'get_fund', 'get_investor', 'amount_received', 'received_date')

    def get_fund(self, obj):
        return obj.capital_call.fund
    get_fund.short_description = 'Fund'

    def get_investor(self, obj):
        return obj.capital_call.investor
    get_investor.short_description = 'Investor'