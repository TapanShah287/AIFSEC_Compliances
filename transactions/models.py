from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError

class TransactionBase(models.Model):
    """
    Abstract base class for all AIF transactions.
    Updated for Multi-Currency support: tracks the original currency 
    and the exchange rate to the Fund's functional currency.
    """
    fund = models.ForeignKey('funds.Fund', on_delete=models.CASCADE)
    
    # The currency in which the actual cash flow/trade occurred
    transaction_currency = models.ForeignKey(
        'currencies.Currency', 
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Currency of the actual cash flow/trade"
    )
    
    # Rate used to convert Transaction Currency -> Fund Functional Currency
    exchange_rate = models.DecimalField(
        max_digits=20, 
        decimal_places=10, 
        default=Decimal('1.0000000000'),
        help_text="Exchange rate to convert to Fund's functional currency"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

# =========================================================
#  1. PORTFOLIO TRADES (Investments & Exits)
# =========================================================

class PurchaseTransaction(TransactionBase):
    investee_company = models.ForeignKey('investee_companies.InvesteeCompany', on_delete=models.CASCADE, related_name='purchases')
    share_capital = models.ForeignKey('investee_companies.ShareCapital', on_delete=models.SET_NULL, null=True, blank=True)
    
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    price = models.DecimalField(max_digits=18, decimal_places=4, help_text="Price per share (in Txn Currency)")
    
    # Calculated Fields
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, editable=False)
    amount_fund_currency = models.DecimalField(max_digits=18, decimal_places=2, default=0, editable=False)
    
    trade_date = models.DateField(default=timezone.now)
    settle_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.price
        self.amount_fund_currency = self.amount * self.exchange_rate
        super().save(*args, **kwargs)

class RedemptionTransaction(TransactionBase):
    investee_company = models.ForeignKey('investee_companies.InvesteeCompany', on_delete=models.CASCADE, related_name='redemptions')
    share_capital = models.ForeignKey('investee_companies.ShareCapital', on_delete=models.SET_NULL, null=True, blank=True)
    
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    price = models.DecimalField(max_digits=18, decimal_places=4, help_text="Selling price per share")
    
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, editable=False)
    amount_fund_currency = models.DecimalField(max_digits=18, decimal_places=2, default=0, editable=False)
    
    trade_date = models.DateField(default=timezone.now)
    # Added to fix consistency with PurchaseTransaction
    settle_date = models.DateField(null=True, blank=True)

    # FIFO / Tax Fields
    cost_basis = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    realized_gain = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.price
        self.amount_fund_currency = self.amount * self.exchange_rate
        super().save(*args, **kwargs)

# =========================================================
#  2. INVESTOR CAPITAL (Liabilities/Equity)
# =========================================================

class InvestorCommitment(TransactionBase):
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='commitments')
    amount_committed = models.DecimalField(max_digits=18, decimal_places=2)
    amount_committed_fund_ccy = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    commitment_date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.amount_committed_fund_ccy = self.amount_committed * self.exchange_rate
        super().save(*args, **kwargs)

class CapitalCall(TransactionBase):
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='capital_calls')
    amount_called = models.DecimalField(max_digits=18, decimal_places=2)
    amount_called_fund_ccy = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    call_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        self.amount_called_fund_ccy = self.amount_called * self.exchange_rate
        super().save(*args, **kwargs)

class DrawdownReceipt(TransactionBase):
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='drawdown_receipts')
    # Link to the call being paid
    capital_call = models.ForeignKey(CapitalCall, on_delete=models.PROTECT, related_name='receipts', null=True, blank=True)
    
    amount_received = models.DecimalField(max_digits=18, decimal_places=2)
    amount_received_fund_ccy = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    receipt_date = models.DateField(default=timezone.now)
    reference = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        self.amount_received_fund_ccy = self.amount_received * self.exchange_rate
        super().save(*args, **kwargs)

class Distribution(TransactionBase):
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='distributions')
    
    gross_amount = models.DecimalField(max_digits=18, decimal_places=2)
    gross_amount_fund_ccy = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    tax_withheld = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    paid_date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.gross_amount_fund_ccy = self.gross_amount * self.exchange_rate
        super().save(*args, **kwargs)

    @property
    def net_amount(self):
        return self.gross_amount - self.tax_withheld

class InvestorUnitIssue(TransactionBase):
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='units')
    units_issued = models.DecimalField(max_digits=18, decimal_places=4)
    nav_at_issue = models.DecimalField(max_digits=18, decimal_places=4)
    issue_date = models.DateField(default=timezone.now)
    is_demat = models.BooleanField(default=False)
    reference = models.CharField(max_length=100, blank=True)
    