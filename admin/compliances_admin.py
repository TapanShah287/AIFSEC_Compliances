from django.contrib import admin
from .models import ComplianceTask, ComplianceDocument

@admin.register(ComplianceTask)
class ComplianceTaskAdmin(admin.ModelAdmin):
    list_display = ("id","fund","company","transaction","topic","due_date","status","final_completion_date")
    list_filter = ("status","fund","company","topic")
    date_hierarchy = "due_date"

@admin.register(ComplianceDocument)
class ComplianceDocumentAdmin(admin.ModelAdmin):
    list_display = ("id","task","uploaded_by","uploaded_at","file")
    date_hierarchy = "uploaded_at"
    list_filter = ("uploaded_by",)