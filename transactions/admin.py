from django.contrib import admin
from .models import PurchaseTransaction, RedemptionTransaction, InvestorCommitment, CapitalCall, DrawdownReceipt, Distribution, InvestorUnitIssue
admin.site.register(PurchaseTransaction)
admin.site.register(RedemptionTransaction)
admin.site.register(InvestorCommitment)
admin.site.register(CapitalCall)
admin.site.register(DrawdownReceipt)
admin.site.register(Distribution)
admin.site.register(InvestorUnitIssue)
