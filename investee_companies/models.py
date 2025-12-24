from django.db import models
from django.utils import timezone
from decimal import Decimal

class InvesteeCompany(models.Model):
    name = models.CharField(max_length=255, unique=True)
    cin = models.CharField(max_length=21, unique=True, verbose_name="CIN", blank=True, null=True)
    incorporation_date = models.DateField(null=True, blank=True)
    sector = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Financial summary (denormalized for quick access)
    total_funding_raised = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    def __str__(self):
        return self.name

class ShareCapital(models.Model):
    """
    Defines the Capital Structure / Instruments.
    e.g. Series A Equity, Seed Preference, etc.
    """
    SHARE_TYPE_CHOICES = [
        ('EQUITY', 'Equity Shares'),
        ('PREF', 'Preference Shares'),
        ('CCPS', 'Compulsorily Convertible Preference'),
        ('OCPS', 'Optionally Convertible Preference'),
        ('CCD', 'Compulsorily Convertible Debentures'),
    ]
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE, related_name='share_classes')
    share_type = models.CharField(max_length=10, choices=SHARE_TYPE_CHOICES, default='EQUITY')
    class_name = models.CharField(max_length=50, help_text="e.g. Series A, Common", default="Common")
    
    # Critical for Corporate Actions (Splits adjust this)
    face_value = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    authorized_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    issued_shares = models.DecimalField(max_digits=18, decimal_places=4, default=0, verbose_name="Total Issued Units")
    as_on_date = models.DateField(default=timezone.now, verbose_name="Structure As On")


    def __str__(self):
        return f"{self.investee_company.name} - {self.class_name} ({self.get_share_type_display()})"

class Shareholding(models.Model):
    """
    The Cap Table Ledger.
    Links an Investor (or manual name) to a specific Share Class and Quantity.
    """
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE)
    investor = models.ForeignKey('investors.Investor', on_delete=models.SET_NULL, null=True, blank=True)
    holder_name = models.CharField(max_length=255, blank=True, help_text="Manual entry for non-AIF holders")
    share_capital = models.ForeignKey(ShareCapital, on_delete=models.CASCADE, related_name='holdings')
    number_of_shares = models.DecimalField(max_digits=18, decimal_places=4)

    def __str__(self):
        return f"{self.display_holder} - {self.number_of_shares} shares"

    @property
    def display_holder(self):
        return self.investor.name if self.investor else self.holder_name

    @property
    def total_capital_value(self):
        """Calculates value based on current Face Value (Units * Face Value)"""
        return self.number_of_shares * self.share_capital.face_value

class CorporateAction(models.Model):
    """
    Audit trail for Bonus Issues, Splits, and Mergers.
    """
    ACTION_TYPES = [
        ('SPLIT', 'Stock Split'), 
        ('BONUS', 'Bonus Issue'), 
        ('MERGER', 'Merger / Amalgamation')
    ]
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE, related_name='corporate_actions')
    
    # Specific class affected (e.g., Bonus issued only to Equity holders)
    target_class = models.ForeignKey(ShareCapital, on_delete=models.CASCADE, null=True, blank=True)
    
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    action_date = models.DateField()
    
    # Ratio Logic: e.g. 1:10 Split = ratio_from 1, ratio_to 10
    ratio_from = models.IntegerField(default=1)
    ratio_to = models.IntegerField(default=1)
    
    # Tracks if the ledger has been updated for this action
    is_executed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_action_type_display()} ({self.ratio_from}:{self.ratio_to})"

class ValuationReport(models.Model):
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE)
    valuation_date = models.DateField()
    report_file = models.FileField(upload_to='valuations/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Valuation {self.investee_company.name} @ {self.valuation_date}"

class ShareValuation(models.Model):
    """
    Links a specific per-share value to a Share Class within a Valuation Report.
    """
    valuation_report = models.ForeignKey(ValuationReport, on_delete=models.CASCADE, related_name='share_values')
    share_capital = models.ForeignKey(ShareCapital, on_delete=models.CASCADE)
    per_share_value = models.DecimalField(max_digits=18, decimal_places=4)

    def __str__(self):
        return f"{self.share_capital} @ {self.per_share_value}"

class CompanyFinancials(models.Model):
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE, related_name='financials')
    financial_year = models.CharField(max_length=9, help_text="e.g. 2023-2024")
    revenue = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    ebitda = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=18, decimal_places=2, default=0)