from django.contrib import admin
from .models import Investor

@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ("id","name","investor_type","kyc_status","pan","contact_email","created_at")
    list_filter = ("investor_type","kyc_status",)
    search_fields = ("name","pan","contact_email")
    ordering = ("name",)