from django.contrib import admin
from .models import ComplianceTask, ComplianceDocument

@admin.register(ComplianceTask)
class ComplianceTaskAdmin(admin.ModelAdmin):
    # Updated list_display to use helper methods for company and transaction
    list_display = ("id", "fund", "get_company", "get_transaction", "topic", "due_date", "status", "final_completion_date")
    # Removed 'company' from list_filter (it's not a direct field)
    list_filter = ("status", "fund", "topic")
    date_hierarchy = "due_date"

    @admin.display(description="Company")
    def get_company(self, obj):
        if obj.purchase_transaction and obj.purchase_transaction.investee_company:
            return obj.purchase_transaction.investee_company.name
        if obj.redemption_transaction and obj.redemption_transaction.investee_company:
            return obj.redemption_transaction.investee_company.name
        return "-"

    @admin.display(description="Transaction")
    def get_transaction(self, obj):
        if obj.purchase_transaction:
            return f"Purchase #{obj.purchase_transaction.id}"
        if obj.redemption_transaction:
            return f"Redemption #{obj.redemption_transaction.id}"
        return "-"

@admin.register(ComplianceDocument)
class ComplianceDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "uploaded_by", "uploaded_at", "file")
    date_hierarchy = "uploaded_at"
    list_filter = ("uploaded_by",)