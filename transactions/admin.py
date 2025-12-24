from django.contrib import admin
from .models import (
    PurchaseTransaction, RedemptionTransaction,
    InvestorCommitment, CapitalCall, DrawdownReceipt, 
    Distribution, InvestorUnitIssue
)

@admin.register(PurchaseTransaction)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'fund', 'investee_company', 'quantity', 'price', 'trade_date')
    list_filter = ('fund', 'investee_company')

@admin.register(RedemptionTransaction)
class RedemptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'fund', 'investee_company', 'quantity', 'price', 'trade_date', 'realized_gain')
    list_filter = ('fund', 'investee_company')

@admin.register(InvestorCommitment)
class CommitmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'fund', 'investor', 'amount_committed', 'commitment_date')
    search_fields = ('investor__name',)

@admin.register(CapitalCall)
class CapitalCallAdmin(admin.ModelAdmin):
    list_display = ('id', 'fund', 'investor', 'amount_called', 'call_date')
    list_filter = ('fund',)

@admin.register(DrawdownReceipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'fund', 'investor', 'amount_received', 'receipt_date')

@admin.register(Distribution)
class DistributionAdmin(admin.ModelAdmin):
    list_display = ('id', 'fund', 'investor', 'gross_amount', 'paid_date')

@admin.register(InvestorUnitIssue)
class UnitIssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'fund', 'investor', 'units_issued', 'nav_at_issue')