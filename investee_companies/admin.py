from django.contrib import admin
from .models import (
    InvesteeCompany, ShareCapital, Shareholding, 
    ValuationReport, ShareValuation, CorporateAction, 
    CompanyFinancials
)

class ShareCapitalInline(admin.TabularInline):
    model = ShareCapital
    extra = 0
    min_num = 1

class ShareholdingInline(admin.TabularInline):
    model = Shareholding
    extra = 0
    autocomplete_fields = ['investor'] # Assumes investor search enabled

@admin.register(InvesteeCompany)
class InvesteeCompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "cin", "incorporation_date", "sector")
    search_fields = ("name", "cin")
    inlines = [ShareCapitalInline, ShareholdingInline]

@admin.register(ShareCapital)
class ShareCapitalAdmin(admin.ModelAdmin):
    list_display = ("investee_company", "class_name", "share_type", "face_value", "authorized_capital")
    list_filter = ("share_type", "investee_company")
    search_fields = ("investee_company__name", "class_name")

@admin.register(Shareholding)
class ShareholdingAdmin(admin.ModelAdmin):
    list_display = ("investee_company", "display_holder", "share_capital", "number_of_shares")
    search_fields = ("investee_company__name", "holder_name", "investor__name")
    list_filter = ("investee_company",)
    autocomplete_fields = ['investor']

@admin.register(ValuationReport)
class ValuationReportAdmin(admin.ModelAdmin):
    list_display = ("investee_company", "valuation_date")
    list_filter = ("investee_company",)

@admin.register(ShareValuation)
class ShareValuationAdmin(admin.ModelAdmin):
    list_display = ("valuation_report", "share_capital", "per_share_value")
    list_filter = ("valuation_report__investee_company",)

@admin.register(CorporateAction)
class CorporateActionAdmin(admin.ModelAdmin):
    list_display = ("investee_company", "action_type", "action_date", "is_executed", "ratio_from", "ratio_to")
    list_filter = ("action_type", "is_executed", "investee_company")
    search_fields = ("investee_company__name",)

@admin.register(CompanyFinancials)
class CompanyFinancialsAdmin(admin.ModelAdmin):
    # FIXED: Changed 'pat' to 'net_profit' to match the model definition
    list_display = ("investee_company", "financial_year", "revenue", "net_profit")
    list_filter = ("financial_year", "investee_company")
    search_fields = ("investee_company__name",)