from django.contrib import admin
from .models import PurchaseTransaction, RedemptionTransaction, CapitalCall, DrawdownReceipt, Distribution

@admin.register(PurchaseTransaction)
class PurchaseTransactionAdmin(admin.ModelAdmin):
    list_display = ("id","fund","company","share_class","quantity","price","trade_date","settle_date")
    date_hierarchy = "trade_date"
    list_filter = ("fund","company","share_class")

@admin.register(RedemptionTransaction)
class RedemptionTransactionAdmin(admin.ModelAdmin):
    list_display = ("id","fund","company","share_class","quantity","price","trade_date")
    date_hierarchy = "trade_date"
    list_filter = ("fund","company","share_class")

@admin.register(CapitalCall)
class CapitalCallAdmin(admin.ModelAdmin):
    list_display = ("id","fund","call_date","amount_called","reference")
    date_hierarchy = "call_date"
    list_filter = ("fund",)

@admin.register(DrawdownReceipt)
class DrawdownReceiptAdmin(admin.ModelAdmin):
    list_display = ("id","fund","investor","receipt_date","amount_received","reference")
    date_hierarchy = "receipt_date"
    list_filter = ("fund","investor")

@admin.register(Distribution)
class DistributionAdmin(admin.ModelAdmin):
    list_display = ("id","fund","investor","paid_date","gross_amount","tax_withheld")
    date_hierarchy = "paid_date"
    list_filter = ("fund","investor")