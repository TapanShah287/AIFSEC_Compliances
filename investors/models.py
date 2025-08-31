# investors/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from taggit.managers import TaggableManager

class Investor(models.Model):
    INVESTOR_TYPES = [
        ("SPONSOR", "Sponsor / Manager"),
        ("LP", "Limited Partner (Investor)"),
        ("OTHER", "Other"),
    ]

    name = models.CharField(max_length=255)
    pan = models.CharField(max_length=10, blank=True, null=True, help_text="PAN of Investor")
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    type = models.CharField(max_length=20, choices=INVESTOR_TYPES, default="LP")
    tags = TaggableManager(blank=True)

    @property
    def total_commitments(self):
        from transactions.models import InvestorCommitment
        return InvestorCommitment.objects.filter(investor=self).aggregate(
            total=Sum("amount_committed")
        )["total"] or Decimal("0.00")

    @property
    def invested_funds(self):
        from transactions.models import InvestorCommitment
        return [c.fund for c in InvestorCommitment.objects.filter(investor=self).select_related("fund")]


    def __str__(self):
        return self.name

class KYCStatus(models.Model):
    INVESTOR_TYPE_CHOICES = [
        ('IND', 'Individual'),
        ('NON-IND', 'Non-Individual'),
    ]

    investor = models.OneToOneField(Investor, on_delete=models.CASCADE, related_name='kyc_status')
    kyc_status = models.BooleanField(default=False, verbose_name="KYC Completed")
    investor_type = models.CharField(max_length=10, choices=INVESTOR_TYPE_CHOICES)
    date_completed = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"KYC for {self.investor.name}"

class FATCADeclaration(models.Model):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='fatca_declarations')
    declaration_status = models.BooleanField(default=False, verbose_name="FATCA Declaration Submitted")
    date_submitted = models.DateField(default=timezone.now)
    is_us_person = models.BooleanField(default=False, verbose_name="Is a US Person")

    def __str__(self):
        return f"FATCA Declaration for {self.investor.name}"

class InvestorDocument(models.Model):
    DOC_TYPES = [
        ("ACCOUNT_FORM", "Account Form"),
        ("PAN", "PAN"),
        ("AADHAR", "Aadhar"),
        ("MOA", "Memorandum of Association"),
        ("AOA", "Articles of Association"),
        ("COI", "Certificate of Incorporation"),
        ("OTHER", "Other"),
    ]
    investor = models.ForeignKey("Investor", on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=32, choices=DOC_TYPES)
    file = models.FileField(upload_to="investors/%Y/%m/%d/")
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("investor", "doc_type")]  # one of each type (optional)
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.get_doc_type_display()} - {self.investor_id}"

class CommunicationLog(models.Model):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='communications')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    communication_date = models.DateField(default=timezone.now)
    COMMUNICATION_TYPES = [('EMAIL', 'Email'), ('CALL', 'Call'), ('MEETING', 'Meeting')]
    communication_type = models.CharField(max_length=10, choices=COMMUNICATION_TYPES)
    notes = models.TextField()

    class Meta:
        ordering = ['-communication_date']

    def __str__(self):
        return f"{self.get_communication_type_display()} with {self.investor.name} on {self.communication_date}"

class InvestorBankAccount(models.Model):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=11, verbose_name="IFSC Code")
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number} for {self.investor.name}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            InvestorBankAccount.objects.filter(investor=self.investor).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)