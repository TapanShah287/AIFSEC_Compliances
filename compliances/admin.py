from django.contrib import admin
from .models import ComplianceMaster, ComplianceTask, ComplianceDocument

# --- Inline for Documents ---
class ComplianceDocumentInline(admin.TabularInline):
    model = ComplianceDocument
    extra = 1

# --- 1. The New Master Rules Engine ---
@admin.register(ComplianceMaster)
class ComplianceMasterAdmin(admin.ModelAdmin):
    # This lets you see the rules clearly
    list_display = ('title', 'jurisdiction', 'scope', 'frequency', 'days_after_period', 'first_due_date')
    
    # Filters to quickly find "SEBI" rules or "Quarterly" rules
    list_filter = ('jurisdiction', 'scope', 'frequency')
    
    search_fields = ('title', 'description')
    
    # Organized layout for adding new rules
    fieldsets = (
        ('Regulation Details', {
            'fields': ('title', 'description', 'jurisdiction', 'frequency')
        }),
        ('Applicability', {
            'fields': ('scope', 'applicable_categories'),
            'description': "Select who this rule applies to (Funds vs. Manager) and which specific categories."
        }),
        ('Deadlines', {
            'fields': ('days_after_period', 'first_due_date'),
            'description': "How many days after the period end is this due?"
        }),
    )

# --- 2. The Task List (Execution) ---
@admin.register(ComplianceTask)
class ComplianceTaskAdmin(admin.ModelAdmin):
    # We added 'manager' and a helper for 'jurisdiction'
    list_display = ('title', 'get_jurisdiction', 'due_date', 'status', 'manager', 'fund', 'priority')
    
    # Updated filters to include Manager and the Master Rule's properties
    list_filter = ('status', 'priority', 'compliance_master__jurisdiction', 'manager', 'fund')
    
    search_fields = ('title', 'description', 'fund__name', 'manager__name')
    date_hierarchy = 'due_date'
    
    inlines = [ComplianceDocumentInline]
    
    # Helper: Fetch Jurisdiction from the related Master Rule
    @admin.display(description='Jurisdiction', ordering='compliance_master__jurisdiction')
    def get_jurisdiction(self, obj):
        return obj.compliance_master.jurisdiction if obj.compliance_master else '-'

# --- 3. Documents ---
@admin.register(ComplianceDocument)
class ComplianceDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'uploaded_at', 'uploaded_by')
    list_filter = ('uploaded_at',)
    search_fields = ('title', 'task__title')