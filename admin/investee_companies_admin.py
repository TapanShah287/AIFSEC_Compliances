from django.contrib import admin
from investee_companies.models import InvesteeCompany, ShareCapital, ShareValuation, ValuationReport, CorporateAction, CompanyFinancials, Shareholding

@admin.register(InvesteeCompany)
class InvesteeCompanyAdmin(admin.ModelAdmin):
    list_display = ("id","name","incorporation_date","cin")
    search_fields = ("name","cin")
    ordering = ("name",)

@admin.register(ShareCapital)
class ShareCapitalAdmin(admin.ModelAdmin):
    list_display = ("id","investee_company","share_type","face_value","number_of_shares","as_on_date")
    list_filter = ("share_type","as_on_date","investee_company")
    search_fields = ("investee_company__name",)

@admin.register(Shareholding)
class ShareholdingAdmin(admin.ModelAdmin):
    list_display = ("id","investee_company","display_holder","share_type","number_of_shares","face_value")
    list_filter = ("share_type","investee_company")
    search_fields = ("investee_company__name","holder_name","investor__name")

@admin.register(ShareValuation)
class ShareValuationAdmin(admin.ModelAdmin):
    list_display = ("id","valuation_report","share_capital","per_share_value")
    list_filter = ("valuation_report__valuation_date","share_capital__share_type","valuation_report__investee_company")
    autocomplete_fields = ("valuation_report","share_capital")

@admin.register(ValuationReport)
class ValuationReportAdmin(admin.ModelAdmin):
    list_display = ("id","investee_company","valuation_date","total_market_value")
    date_hierarchy = "valuation_date"
    search_fields = ("investee_company__name",)

@admin.register(CorporateAction)
class CorporateActionAdmin(admin.ModelAdmin):
    list_display = ("id","investee_company","action_type","action_date","notes")
    list_filter = ("action_type","action_date")

@admin.register(CompanyFinancials)
class CompanyFinancialsAdmin(admin.ModelAdmin):
    list_display = ("id","investee_company","period_date","revenue","ebitda","net_income")
    date_hierarchy = "period_date"
    search_fields = ("investee_company__name",)
