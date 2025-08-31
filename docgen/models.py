from django.db import models
class DocumentTemplate(models.Model):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="docgen/templates/")
    description = models.TextField(blank=True, null=True)
    sample_context = models.JSONField(blank=True, null=True)
    def __str__(self): return f"{self.code} — {self.name}"
class GeneratedDocument(models.Model):
    template = models.ForeignKey(DocumentTemplate, on_delete=models.PROTECT, related_name="generated_docs")
    file = models.FileField(upload_to="docgen/generated/")
    pdf_file = models.FileField(upload_to="docgen/generated/", null=True, blank=True)
    context = models.JSONField(default=dict, blank=True)
    fund = models.ForeignKey("funds.Fund", on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_documents")
    investor = models.ForeignKey("investors.Investor", on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_documents")
    investee_company = models.ForeignKey("investee_companies.InvesteeCompany", on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_documents")
    purchase_transaction = models.ForeignKey("transactions.PurchaseTransaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_documents")
    redemption_transaction = models.ForeignKey("transactions.RedemptionTransaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_documents")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.template.code} | {self.file.name}"
