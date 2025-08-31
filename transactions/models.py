# transactions/models.py
import hashlib
from django.db import models
from django.db.models import Sum, Q
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from functools import cached_property

# Imports from other apps
from funds.models import Fund
from investee_companies.models import InvesteeCompany, Shareholding


class Transaction(models.Model):
    def __str__(self):
        return f"Purchase of {self.quantity} shares in {self.investee_company.name} by {self.fund.name}"


class PurchaseTransaction(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='purchases')
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE, related_name='purchases_by_fund')
    share_capital = models.ForeignKey(Shareholding, on_delete=models.SET_NULL, null=True, blank=True)

    quantity = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="Qty of Shares")
    purchase_rate = models.DecimalField(max_digits=18, decimal_places=4)
    face_value = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    purchase_date = models.DateField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=(
        ('draft','Draft'), ('posted','Posted'), ('reversed','Reversed')
    ), default='posted')
    import_batch_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    external_ref = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    notes = models.TextField(null=True, blank=True)
    fees = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    taxes = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    currency = models.CharField(max_length=3, default='INR')
    fx_rate = models.DecimalField(max_digits=18, decimal_places=6, default=1)
    unique_hash = models.CharField(max_length=64, db_index=True, editable=False)

    @property
    def amount(self):
        return (self.quantity or 0) * (self.purchase_rate or 0)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-purchase_date', '-id']
    
    def __str__(self):
        return f"Purchase of {self.quantity} shares in {self.investee_company.name} by {self.fund.name}"


class RedemptionTransaction(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='redemptions')
    investee_company = models.ForeignKey(InvesteeCompany, on_delete=models.CASCADE, related_name='redemptions_by_fund')
    share_capital = models.ForeignKey(Shareholding, on_delete=models.SET_NULL, null=True, blank=True)

    quantity = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="Qty of Shares")
    redemption_rate = models.DecimalField(max_digits=18, decimal_places=4)
    redemption_date = models.DateField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=(
        ('draft','Draft'), ('posted','Posted'), ('reversed','Reversed')
    ), default='posted')
    import_batch_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    external_ref = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    notes = models.TextField(null=True, blank=True)
    fees = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    taxes = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    currency = models.CharField(max_length=3, default='INR')
    fx_rate = models.DecimalField(max_digits=18, decimal_places=6, default=1)

    @property
    def amount(self):
        return (self.quantity or 0) * (self.redemption_rate or 0)

    @cached_property
    def cost_basis(self):
        from .utils import calculate_fifo_cost_basis
        if not self.pk:
            return Decimal('0.0')
        return calculate_fifo_cost_basis(self)

    @cached_property
    def capital_gain(self):
        return self.amount - self.cost_basis

    def clean(self):
        if self.quantity and self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be a positive number.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-redemption_date', '-id']

    def __str__(self):
        return f"Redemption of {self.quantity} shares from {self.investee_company.name} by {self.fund.name}"


class InvestorCommitment(models.Model):
    fund = models.ForeignKey('funds.Fund', on_delete=models.CASCADE, related_name='commitments')
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='commitments')
    commitment_date = models.DateField()
    amount_committed = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        ordering = ['-commitment_date']

    def __str__(self):
        return f"Commitment of {self.amount_committed} by {self.investor} to {self.fund}"


class CapitalCall(models.Model):
    fund = models.ForeignKey('funds.Fund', on_delete=models.CASCADE, related_name='capital_calls')
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='capital_calls')
    call_date = models.DateField()
    amount_called = models.DecimalField(max_digits=18, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-call_date']

    def __str__(self):
        return f"Capital Call of {self.amount_called} from {self.investor} on {self.call_date}"


class DrawdownReceipt(models.Model):
    fund = models.ForeignKey('funds.Fund', on_delete=models.CASCADE, related_name='drawdown_receipts')
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='drawdown_receipts')
    receipt_date = models.DateField()
    amount_received = models.DecimalField(max_digits=18, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-receipt_date']

    def __str__(self):
        return f"Drawdown Receipt of {self.amount_received} from {self.investor} on {self.receipt_date}"


class Distribution(models.Model):
    fund = models.ForeignKey('funds.Fund', on_delete=models.CASCADE, related_name='distributions')
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='distributions')
    distribution_date = models.DateField()
    amount_distributed = models.DecimalField(max_digits=18, decimal_places=2)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-distribution_date']

    def __str__(self):
        return f"Distribution of {self.amount_distributed} to {self.investor} on {self.distribution_date}"

class InvestorUnitIssue(models.Model):
    fund = models.ForeignKey('funds.Fund', on_delete=models.CASCADE, related_name='unit_issues')
    investor = models.ForeignKey('investors.Investor', on_delete=models.CASCADE, related_name='unit_issues')
    issue_date = models.DateField(default=timezone.now)
    units_issued = models.DecimalField(max_digits=18, decimal_places=4)
    price_per_unit = models.DecimalField(max_digits=18, decimal_places=6)
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.units_issued} units to {self.investor.name} @ {self.price_per_unit}"

class Cashflow(models.Model):
    TRANSACTION_TYPES = [
        ("CALL", "Capital Call (Drawdown)"),
        ("DISTRIBUTION", "Distribution / Redemption"),
        ("EXPENSE", "Expense"),
        ("OTHER", "Other"),
    ]

    fund = models.ForeignKey(
        "funds.Fund",
        on_delete=models.CASCADE,
        related_name="cashflows"
    )
    investor = models.ForeignKey(
        "investors.Investor",
        on_delete=models.CASCADE,
        related_name="cashflows",
        null=True, blank=True
    )
    date = models.DateField(default=timezone.now)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.transaction_type} – {self.fund.name} : ₹{self.amount} on {self.date}"