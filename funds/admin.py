from django.contrib import admin
from .models import Fund, NavSnapshot, Document, StewardshipEngagement

@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "corpus", "date_of_inception", "currency")
    list_filter = ("category", "jurisdiction", "currency")
    search_fields = ("name", "sebi_registration_number")
    date_hierarchy = "date_of_inception"

@admin.register(NavSnapshot)
class NavSnapshotAdmin(admin.ModelAdmin):
    list_display = ("fund", "as_on_date", "nav_per_unit", "aum", "is_first_close_nav")
    date_hierarchy = "as_on_date"
    list_filter = ("fund",)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "fund", "investor", "uploaded_at", "is_demat_advice")
    list_filter = ("fund", "is_demat_advice")
    search_fields = ("title", "investor__name")

@admin.register(StewardshipEngagement)
class StewardshipAdmin(admin.ModelAdmin):
    list_display = ("fund", "investee_company", "topic", "status", "engagement_date")
    list_filter = ("status", "fund")