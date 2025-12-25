from django.db import models
from django.utils import timezone
from funds.models import Fund
from investors.models import Investor
from investee_companies.models import InvesteeCompany, ShareCapital
from currencies.models import Currency

class InvestorCommitment(models.Model):
    """
    The contract between Investor and Fund. 
    Defines the total amount they have agreed to invest.
    """
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='commitments')
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='commitments')
    amount_committed = models.DecimalField(max_digits=14, decimal_places=2)
    commitment_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.investor.name} - {self.amount_committed}"

    @property
    def unfunded_amount(self):
        # Calculate total capital called against this investor for this fund
        total_called = CapitalCall.objects.filter(
            fund=self.fund, 
            investor=self.investor
        ).aggregate(models.Sum('amount_called'))['amount_called__sum'] or 0
        return self.amount_committed - total_called

class CapitalCall(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    call_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    amount_called = models.DecimalField(max_digits=14, decimal_places=2)
    purpose = models.CharField(max_length=255)
    reference = models.CharField(max_length=50, unique=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference} - {self.investor.name}"

class DrawdownReceipt(models.Model):
    PAYMENT_MODES = [('NEFT', 'NEFT'), ('RTGS', 'RTGS'), ('SWIFT', 'SWIFT'), ('CHEQUE', 'Cheque')]
    
    capital_call = models.ForeignKey(CapitalCall, on_delete=models.CASCADE, related_name='receipts')
    received_date = models.DateField(default=timezone.now)
    amount_received = models.DecimalField(max_digits=14, decimal_places=2)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODES, default='NEFT')
    transaction_ref = models.CharField(max_length=100, help_text="UTR/IMPS Ref")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rcpt {self.id} - {self.amount_received}"

class InvestorUnitIssue(models.Model):
    """
    Tracks units issued to an investor. 
    Crucial for NAV and Capital Account reporting.
    """
    fund = models.ForeignKey('funds.Fund', on_delete=models.CASCADE)
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE)
    issue_date = models.DateField(default=timezone.now)
    units_issued = models.DecimalField(max_digits=18, decimal_places=4)
    price_per_unit = models.DecimalField(max_digits=18, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.investor.name} - {self.units_issued} Units"


class PurchaseTransaction(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE)
    share_class = models.ForeignKey(ShareCapital, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_date = models.DateField(default=timezone.now)
    quantity = models.DecimalField(max_digits=14, decimal_places=2)
    price_per_share = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_amount(self):
        return self.quantity * self.price_per_share

class RedemptionTransaction(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE)
    share_class = models.ForeignKey(ShareCapital, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_date = models.DateField(default=timezone.now)
    quantity = models.DecimalField(max_digits=14, decimal_places=2)
    price_per_share = models.DecimalField(max_digits=14, decimal_places=2)
    
    # Auto-Calculated Fields
    cost_basis = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    realized_gain = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_proceeds(self):
        return self.quantity * self.price_per_share

class Distribution(models.Model):
    DIST_TYPES = [('INTEREST', 'Interest'), ('DIVIDEND', 'Dividend'), ('PRINCIPAL', 'Principal Return')]
    
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    distribution_date = models.DateField(default=timezone.now)
    gross_amount = models.DecimalField(max_digits=14, decimal_places=2)
    distribution_type = models.CharField(max_length=20, choices=DIST_TYPES, default='PRINCIPAL')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)