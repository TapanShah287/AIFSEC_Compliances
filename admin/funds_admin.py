from django.contrib import admin
from .models import Fund, Commitment, NavSnapshot

@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ("id","name","category","corpus","inception_date","target_close_date")
    list_filter = ("category",)
    search_fields = ("name",)

@admin.register(Commitment)
class CommitmentAdmin(admin.ModelAdmin):
    list_display = ("id","fund","investor","committed_amount","commitment_date","status")
    list_filter = ("fund","status")
    search_fields = ("investor__name",)

@admin.register(NavSnapshot)
class NavSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id","fund","as_on_date","nav_per_unit","aum","units_outstanding")
    date_hierarchy = "as_on_date"
    list_filter = ("fund",)