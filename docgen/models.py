from django.db import models
from django.conf import settings
from django.utils import timezone

class DocumentTemplate(models.Model):
    """
    Stores the .docx template files uploaded by Admin.
    Code is used in views to find the right template (e.g., 'KYC_INDIVIDUAL').
    """
    name = models.CharField(max_length=255)
    code = models.SlugField(unique=True, help_text="Unique code to reference in code (e.g., COMMITMENT_LETTER)")
    file = models.FileField(upload_to='docgen/templates/')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class GeneratedDocument(models.Model):
    """
    Stores the result of the generation process.
    """
    template = models.ForeignKey(DocumentTemplate, on_delete=models.SET_NULL, null=True)
    generated_file = models.FileField(upload_to='docgen/generated/')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    # --- Relationships (Optional Links) ---
    # We use string references to avoid circular imports
    fund = models.ForeignKey('funds.Fund', on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_docs')
    investor = models.ForeignKey('investors.Investor', on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_docs')
    investee_company = models.ForeignKey('investee_companies.InvesteeCompany', on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_docs')
    
    # Link to specific transactions if needed (e.g., for a specific Drawdown Notice)
    capital_call = models.ForeignKey('transactions.CapitalCall', on_delete=models.SET_NULL, null=True, blank=True)
    distribution = models.ForeignKey('transactions.Distribution', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Doc {self.id} - {self.template.code if self.template else 'Custom'}"