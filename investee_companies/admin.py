from django.contrib import admin
from .models import InvesteeCompany, Shareholding, ShareValuation, ValuationReport, CorporateAction, CompanyFinancials
admin.site.register(InvesteeCompany)
admin.site.register(Shareholding)
admin.site.register(ShareValuation)
admin.site.register(ValuationReport)
admin.site.register(CorporateAction)
admin.site.register(CompanyFinancials)
