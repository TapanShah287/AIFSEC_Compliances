# funds/models.py
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

class Fund(models.Model):
    FUND_CATEGORY_CHOICES = [
        ('CAT_I', 'Category I'),
        ('CAT_II', 'Category II'),
        ('CAT_III', 'Category III'),
    ]

    name = models.CharField(max_length=255)
    sebi_registration_number = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=10, choices=FUND_CATEGORY_CHOICES)
    corpus = models.DecimalField(max_digits=18, decimal_places=2, help_text="Total fund corpus in INR")
    date_of_inception = models.DateField(default=timezone.now)

    manager = models.ForeignKey(
        'manager_entities.ManagerEntity',
        on_delete=models.PROTECT,
        related_name='funds',
        help_text='Fund Manager Entity',
        null=True, blank=True,
    )

    def __str__(self):
        return self.name

    # --- Properties for Aggregated Financial Data ---
    @property
    def total_commitments(self):
        from transactions.models import InvestorCommitment
        return InvestorCommitment.objects.filter(fund=self).aggregate(
            total=models.Sum("amount_committed")
        )["total"] or Decimal("0.00")

    @property
    def investor_count(self):
        from transactions.models import InvestorCommitment
        return InvestorCommitment.objects.filter(fund=self).values("investor").distinct().count()
    
    @property
    def total_capital_called(self):
        return self.capital_calls.aggregate(total=Sum('amount_called'))['total'] or Decimal('0.00')

    @property
    def total_drawn(self):
        return self.drawdown_receipts.aggregate(total=Sum('amount_received'))['total'] or Decimal('0.00')
        
    @property
    def total_distributed(self):
        return self.distributions.aggregate(total=Sum('amount_distributed'))['total'] or Decimal('0.00')

    @property
    def total_units_issued(self):
        return self.total_commitment

    @property
    def total_current_value(self):
        total_value = Decimal('0.00')
        portfolio = self.get_portfolio_summary()
        for holding in portfolio:
            if holding.get('investee_company'):
                latest_price = holding['investee_company'].latest_valuation or Decimal('0.00')
                total_value += holding['units'] * latest_price
        return total_value

    @property
    def nav_per_unit(self):
        if self.total_units_issued > 0:
            return self.total_current_value / self.total_units_issued
        return Decimal('0.00')

    def get_portfolio_summary(self):
        from transactions.models import PurchaseTransaction, RedemptionTransaction
        from investee_companies.models import InvesteeCompany
        
        portfolio = {}
        
        purchases = PurchaseTransaction.objects.filter(fund=self).select_related('investee_company').values(
            'investee_company_id', 'investee_company__name'
        ).annotate(total_quantity=Sum('quantity'))
        
        for p in purchases:
            company_id = p['investee_company_id']
            portfolio[company_id] = {
                'name': p['investee_company__name'],
                'units': p['total_quantity']
            }

        redemptions = RedemptionTransaction.objects.filter(fund=self).values(
            'investee_company_id'
        ).annotate(total_quantity=Sum('quantity'))

        for r in redemptions:
            company_id = r['investee_company_id']
            if company_id in portfolio:
                portfolio[company_id]['units'] -= r['total_quantity']
        
        # Fetch investee company objects to access valuation data
        company_ids = list(portfolio.keys())
        companies = InvesteeCompany.objects.in_bulk(company_ids)

        summary = []
        for cid, data in portfolio.items():
            if data['units'] > 0:
                summary.append({
                    'company': data['name'],
                    'units': data['units'],
                    'investee_company': companies.get(cid) # Attach the object
                })
        return summary


class Document(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='documents')
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='fund_documents', null=True, blank=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class NAVHistory(models.Model):
    fund = models.ForeignKey(
        "funds.Fund",
        on_delete=models.CASCADE,
        related_name="nav_history"
    )
    date = models.DateField(default=timezone.now)
    nav_per_unit = models.DecimalField(
        max_digits=18, decimal_places=4,
        help_text="NAV per unit"
    )
    total_aum = models.DecimalField(
        max_digits=18, decimal_places=2,
        help_text="Total Assets Under Management",
        default=Decimal("0.00")
    )

    class Meta:
        unique_together = ("fund", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.fund.name} NAV on {self.date}: {self.nav_per_unit}"


class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.user} - {self.action} at {self.timestamp}'
