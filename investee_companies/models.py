# investee_companies/models.py
from django.db import models
from django.utils import timezone

class InvesteeCompany(models.Model):
    name = models.CharField(max_length=255, unique=True)
    cin = models.CharField(max_length=21, unique=True, verbose_name="Corporate Identification Number")
    incorporation_date = models.DateField()
    
    def __str__(self):
        return self.name

class Shareholding(models.Model):
    SHARE_TYPE_CHOICES = [
        ('EQ', 'Equity Shares'),
        ('PREF', 'Preference Shares'),
        ('CONV', 'Convertible Instruments'),
    ]

    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE, related_name='shareholdings')
    # Link to investors.Investor if available; also store a free-text name for external holders
    investor = models.ForeignKey('investors.Investor', on_delete=models.SET_NULL, null=True, blank=True, related_name='investee_shareholdings')
    holder_name = models.CharField(max_length=255, blank=True, help_text="If not linked to an Investor record, type the shareholder name")
    share_type = models.CharField(max_length=10, choices=SHARE_TYPE_CHOICES, default='EQ')
    number_of_shares = models.PositiveBigIntegerField()
    face_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    acquisition_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True, help_text="Price per share at acquisition (optional)")
    acquisition_date = models.DateField(null=True, blank=True)
    certificate_or_demat = models.CharField(max_length=255, blank=True, help_text="Certificate number or Demat account")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Shareholding"
        verbose_name_plural = "Shareholdings"
        unique_together = [('investee_company','investor','holder_name','share_type')]

    def __str__(self):
        who = self.investor.name if self.investor_id else (self.holder_name or 'Unspecified Holder')
        return f"{who} – {self.number_of_shares} {self.get_share_type_display()} in {self.investee_company.name}"

    @property
    def total_face_value(self):
        return (self.face_value or 0) * (self.number_of_shares or 0)

    def percent_of_class(self):
        """Percent of this shareholding within its share_type for the company."""
        total = Shareholding.objects.filter(investee_company=self.investee_company, share_type=self.share_type)                    .aggregate(models.Sum('number_of_shares'))['number_of_shares__sum'] or 0
        if not total:
            return 0
        return float(self.number_of_shares) * 100.0 / float(total)

    def display_holder(self):
        return self.investor.name if self.investor_id else (self.holder_name or 'Unspecified Holder')


class ValuationReport(models.Model):
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE, related_name='valuation_reports')
    valuation_date = models.DateField(default=timezone.now)
    total_market_value = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    report_file = models.FileField(upload_to='valuation_reports/', null=True, blank=True)

    def __str__(self):
        return f"Valuation for {self.investee_company.name} as of {self.valuation_date}"

class ShareValuation(models.Model):
    valuation_report = models.ForeignKey(ValuationReport, on_delete=models.CASCADE, related_name='share_valuations')
    share_capital = models.ForeignKey(Shareholding, on_delete=models.SET_NULL, null=True, blank=True, related_name='valuations')
    per_share_value = models.DecimalField(max_digits=18, decimal_places=2)

    def __str__(self):
        if self.share_capital:
            return f"{self.share_capital.get_share_type_display()} - ₹{self.per_share_value}"
        return f"Valuation of ₹{self.per_share_value}"

class CorporateAction(models.Model):
    ACTION_CHOICES = [
        ('SPLIT', 'Stock Split'),
        ('BONUS', 'Bonus Issue'),
        ('CONV', 'Conversion'),
    ]
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE, related_name='corporate_actions')
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_date = models.DateField()
    details = models.TextField()

    share_type = models.CharField(max_length=4, choices=Shareholding.SHARE_TYPE_CHOICES, blank=True, null=True)
    ratio = models.CharField(max_length=50, blank=True, null=True)

    from_share_type = models.CharField(max_length=4, choices=Shareholding.SHARE_TYPE_CHOICES, blank=True, null=True)
    to_share_type = models.CharField(max_length=4, choices=Shareholding.SHARE_TYPE_CHOICES, blank=True, null=True)
    number_of_shares_converted = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)

    def __str__(self):
        return f"{self.get_action_type_display()} for {self.investee_company.name} on {self.action_date}"

class CompanyFinancials(models.Model):
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE, related_name='financials')
    period_date = models.DateField(help_text="End date of the financial period, e.g., end of a quarter.")
    revenue = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    ebitda = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True, verbose_name="EBITDA")
    net_income = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-period_date']
        verbose_name_plural = "Company Financials"

    def __str__(self):
        return f"Financials for {self.investee_company.name} for period ending {self.period_date}"
