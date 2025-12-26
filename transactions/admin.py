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
    # Change 'transaction_ref' -> 'transaction_reference'
    # Change 'received_date' -> 'date_received'
    list_display = (
        'transaction_reference', 
        'investor', 
        'fund', 
        'amount_received', 
        'date_received'
    )
    list_filter = ('fund', 'date_received')
    search_fields = ('transaction_reference', 'investor__name')