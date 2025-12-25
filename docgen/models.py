from django.db import models
from django.conf import settings

class DocumentTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('DOCX', 'Word Document (.docx)'),
        ('HTML', 'HTML Layout (for PDF)'),
    ]
    
    name = models.CharField(max_length=255)
    code = models.SlugField(unique=True, help_text="Unique code (e.g. CAPITAL_CALL)")
    type = models.CharField(max_length=10, choices=TEMPLATE_TYPES, default='DOCX')
    
    # Dual storage: File for DOCX, Text for HTML
    file = models.FileField(upload_to='docgen/templates/', blank=True, null=True)
    html_content = models.TextField(blank=True, null=True, help_text="Paste HTML for PDF templates here")
    
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class GeneratedDocument(models.Model):
    template = models.ForeignKey(DocumentTemplate, on_delete=models.SET_NULL, null=True)
    generated_file = models.FileField(upload_to='docgen/generated/%Y/%m/')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    # Smart Links to your existing apps
    fund = models.ForeignKey('funds.Fund', on_delete=models.SET_NULL, null=True, blank=True)
    investor = models.ForeignKey('investors.Investor', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Doc #{self.id} - {self.template.code if self.template else 'Custom'}"