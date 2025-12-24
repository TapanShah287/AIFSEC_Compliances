# investors/models.py
from django.db import models
from django.utils import timezone
from decimal import Decimal

class Investor(models.Model):
    INVESTOR_TYPE_CHOICES = [
        ('INDIVIDUAL', 'Individual'),
        ('HUF', 'HUF'),
        ('COMPANY', 'Corporate Body'),
        ('LLP', 'LLP'),
        ('TRUST', 'Trust'),
        ('NRI', 'NRI'),
        ('FPI', 'FPI / Foreign Entity'),
    ]
    
    KYC_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUBMITTED', 'Submitted'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]

    # NEW: 2025 Accredited Investor Logic
    ACCREDITATION_CHOICES = [
        ('NOT_APPLICABLE', 'Not Applicable'),
        ('VALID', 'Valid Accreditation'),
        ('EXPIRED', 'Accreditation Expired'),
    ]

    name = models.CharField(max_length=255)
    investor_type = models.CharField(max_length=20, choices=INVESTOR_TYPE_CHOICES, default='INDIVIDUAL')
    
    # Contact Info
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    pan = models.CharField(max_length=10, unique=True, help_text="Permanent Account Number")
    
    # NEW: Demat details for unit allotment (SEBI 2025 Mandate)
    demat_account_no = models.CharField(max_length=100, blank=True, null=True)
    dp_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="DP ID")
    
    # NEW: Accreditation Status for AI-Only schemes
    accreditation_status = models.CharField(max_length=20, choices=ACCREDITATION_CHOICES, default='NOT_APPLICABLE')
    accreditation_expiry = models.DateField(null=True, blank=True)
    
    # Status
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='PENDING')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Risk Profiling (2025 Transparency Requirement)
    risk_appetite = models.CharField(max_length=50, choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')], default='MEDIUM')

    def __str__(self):
        return self.name

    @property
    def total_committed(self):
        from transactions.models import InvestorCommitment
        return InvestorCommitment.objects.filter(investor=self).aggregate(
            total=models.Sum('amount_committed')
        )['total'] or Decimal('0.00')

    @property
    def total_contributed(self):
        from transactions.models import DrawdownReceipt
        return DrawdownReceipt.objects.filter(investor=self).aggregate(
            total=models.Sum('amount_received')
        )['total'] or Decimal('0.00')

    @property
    def uncalled_commitment(self):
        return self.total_committed - self.total_contributed

def investor_doc_path(instance, filename):
    return f"investors/{instance.investor.id}/documents/{filename}"

class InvestorDocument(models.Model):
    DOC_TYPES = [
        ('PAN', 'PAN Card'),
        ('AADHAR', 'Aadhar Card'),
        ('PASSPORT', 'Passport'),
        ('BANK_PROOF', 'Bank Proof'),
        ('ACCREDITATION_CERT', 'Accreditation Certificate'), # New for 2025
        ('FATCA_CRS', 'FATCA / CRS Declaration'), # New for 2025
        ('OTHER', 'Other'),
    ]
    
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    file = models.FileField(upload_to=investor_doc_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_doc_type_display()} - {self.investor.name}"