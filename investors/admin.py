from django.contrib import admin
from .models import Investor, InvestorDocument

class DocumentInline(admin.TabularInline):
    model = InvestorDocument
    extra = 0

@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ("name", "investor_type", "kyc_status", "email", "total_committed")
    list_filter = ("investor_type", "kyc_status")
    search_fields = ("name", "email", "pan")
    inlines = [DocumentInline]