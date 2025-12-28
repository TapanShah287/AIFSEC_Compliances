from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from django.db.models import Sum, F
from django.core.validators import MinValueValidator
from manager_entities.models import ManagerEntity


class Fund(models.Model):
    # --- Choices ---
    FUND_CATEGORY_CHOICES = [
        ('CAT_I', 'Category I (Venture/Social)'),
        ('CAT_II', 'Category II (PE/Debt)'),
        ('CAT_III', 'Category III (Hedge/Public)'),
    ]

    JURISDICTION_CHOICES = [
        ('DOMESTIC', 'SEBI (Domestic)'),
        ('IFSC', 'IFSCA (GIFT City)'),
    ]

    SCHEME_TYPE_CHOICES = [
        ('MAIN', 'Main AIF Scheme'),
        ('CIV', 'Co-Investment Vehicle (CIV)'),
        ('ANGEL', 'Angel Fund Segment'),
        ('AI_ONLY', 'Accredited Investor Only Fund'), # New 2025 Category
    ]

    # --- Basic Info ---
    name = models.CharField(max_length=255)
    sebi_registration_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # --- Strategy & Structure ---
    category = models.CharField(max_length=20, choices=FUND_CATEGORY_CHOICES, default='CAT_II')
    jurisdiction = models.CharField(max_length=20, choices=JURISDICTION_CHOICES, default='DOMESTIC')
    scheme_type = models.CharField(max_length=20, choices=SCHEME_TYPE_CHOICES, default='MAIN')
    
    # Financials
    # We use string reference to 'currencies.Currency' to avoid circular imports
    currency = models.ForeignKey(
        'currencies.Currency', 
        on_delete=models.PROTECT, 
        related_name='funds',
        default=1, # Ensure you have an INR record with ID 1
        help_text="Functional currency of the fund"
    )
    
    corpus = models.DecimalField(
        max_digits=20, decimal_places=2, 
        help_text="Target Fund Size",
        default=Decimal('0.00')
    )
    sponsor_commitment = models.DecimalField(
        max_digits=20, decimal_places=2,
        help_text="Manager's Skin in the Game",
        default=Decimal('0.00')
    )

    # --- Relationships ---
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_funds'
    )

    manager_entity = models.ForeignKey(
        ManagerEntity,
        on_delete=models.PROTECT,
        related_name="funds",
        help_text="Manager entity under which this fund is registered",
        null=False,
        blank=False,
    )
    
    # Self-referential for CIVs (Co-Investment Vehicles link to Main Fund)
    parent_fund = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, blank=True, 
        related_name='child_schemes'
    )

    # --- Timeline ---
    date_of_inception = models.DateField(default=timezone.now)
    target_close_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    @property
    def total_committed(self):
        return self.commitments.aggregate(s=Sum('amount_committed'))['s'] or 0

    @property
    def total_called(self):
        # Requires import from transactions.models inside the method to avoid circular import
        from transactions.models import CapitalCall
        return CapitalCall.objects.filter(fund=self).aggregate(s=Sum('amount_called'))['s'] or 0

    @property
    def total_invested_capital(self):
        from transactions.models import PurchaseTransaction
        return PurchaseTransaction.objects.filter(fund=self).aggregate(s=Sum(F('quantity') * F('price_per_share')))['s'] or 0

    @property
    def raised_percentage(self):
        if self.corpus > 0:
            return (self.total_committed / self.corpus) * 100
        return 0

    @property
    def drawdown_percentage(self):
        committed = self.total_committed
        if committed > 0:
            return (self.total_called / committed) * 100
        return 0

class NavSnapshot(models.Model):
    """
    Quarterly/Monthly NAV records for Performance Reporting.
    """
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='nav_history')
    as_on_date = models.DateField()
    
    nav_per_unit = models.DecimalField(max_digits=15, decimal_places=4)
    aum = models.DecimalField(max_digits=20, decimal_places=2, help_text="Assets Under Management")
    units_outstanding = models.DecimalField(max_digits=18, decimal_places=4)
    
    is_first_close_nav = models.BooleanField(default=False, help_text="Is this the NAV at First Close?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-as_on_date']
        unique_together = ['fund', 'as_on_date']

    def __str__(self):
        return f"{self.fund.name} - {self.as_on_date}: {self.nav_per_unit}"


class Document(models.Model):
    """
    Fund documents and Investor-specific compliance docs (Demat Advice).
    """
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='documents')
    investor = models.ForeignKey(
        'investors.Investor', 
        on_delete=models.CASCADE, 
        related_name='fund_documents', 
        null=True, blank=True
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='fund_documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # 2025 Compliance
    is_demat_advice = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class StewardshipEngagement(models.Model):
    """
    Mandatory for IFSCA Funds & optional for SEBI Cat-II/III.
    Tracks 'Active Engagement' with portfolio companies.
    """
    STATUS_CHOICES = [
        ('OPEN', 'Open/Ongoing'),
        ('RESOLVED', 'Resolved/Closed'),
        ('ESCALATED', 'Escalated to Board'),
    ]

    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='stewardship_logs')
    investee_company = models.ForeignKey('investee_companies.InvesteeCompany', on_delete=models.CASCADE)
    
    engagement_date = models.DateField(default=timezone.now)
    topic = models.CharField(max_length=255, help_text="e.g. ESG, Governance, Strategy")
    description = models.TextField()
    outcome = models.TextField(blank=True, help_text="Result of the intervention")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')

    def __str__(self):
        return f"{self.fund.name} -> {self.investee_company.name}: {self.topic}"

class InvestorPosition(models.Model):
    """
    The Cap Table Entry. 
    Represents an investor's total holding in this specific Fund.
    """
    fund = models.ForeignKey('funds.Fund', on_delete=models.CASCADE, related_name='cap_table')
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='holdings')
    
    # The essential numbers
    total_units = models.DecimalField(max_digits=20, decimal_places=4, default=Decimal('0.0000'))
    total_capital_contributed = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('fund', 'investor')
        verbose_name = "Cap Table Entry"
        verbose_name_plural = "Cap Table Entries"

    @property
    def ownership_percentage(self):
        """Calculates the investor's stake relative to the total fund units."""
        # Get total units for this fund
        total = InvestorPosition.objects.filter(fund=self.fund).aggregate(
            models.Sum('total_units')
        )['total_units__sum']
        
        if total and total > 0:
            return (self.total_units / total) * 100
        return 0

    def __str__(self):
        return f"{self.fund.name} - {self.investor.name} ({self.total_units} Units)"

class UnitIssuance(models.Model):
    """
    The Event.
    Records exactly when and why units were added to the Cap Table.
    """
    # Link to the specific line item on the Cap Table
    position = models.ForeignKey(InvestorPosition, on_delete=models.CASCADE, related_name='issuances')
    
    # Link to the Money (Lazy reference to avoid circular imports)
    receipt = models.OneToOneField('transactions.DrawdownReceipt', on_delete=models.CASCADE, related_name='unit_issuance')
    
    # The Math
    units_issued = models.DecimalField(max_digits=20, decimal_places=4)
    nav_at_issuance = models.DecimalField(max_digits=12, decimal_places=4)
    date_issued = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"+{self.units_issued} Units (NAV: {self.nav_at_issuance})"