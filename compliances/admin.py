from django.contrib import admin
from .models import ComplianceTask, ComplianceDocument

class ComplianceDocumentInline(admin.TabularInline):
    model = ComplianceDocument
    extra = 1

@admin.register(ComplianceTask)
class ComplianceTaskAdmin(admin.ModelAdmin):
    # FIXED: Updated field names to match the new Model
    list_display = ('title', 'fund', 'jurisdiction', 'due_date', 'status', 'priority', 'assigned_to', 'completion_date')
    
    # FIXED: Removed 'topic', added valid filters
    list_filter = ('status', 'jurisdiction', 'priority', 'fund')
    
    search_fields = ('title', 'description', 'fund__name')
    date_hierarchy = 'due_date'
    inlines = [ComplianceDocumentInline]

@admin.register(ComplianceDocument)
class ComplianceDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('title', 'task__title')