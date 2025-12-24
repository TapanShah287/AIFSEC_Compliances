from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import CapitalCall, DrawdownReceipt, InvestorUnitIssue, InvestorCommitment
from funds.models import NavSnapshot

class TransactionService:
    
    @staticmethod
    @transaction.atomic
    def process_drawdown(receipt: DrawdownReceipt):
        """
        Orchestrates the post-receipt workflow:
        1. Auto-matches receipt to oldest pending Capital Calls (FIFO).
        2. Issues Units (either New Units or increasing Paid-Up value).
        """
        
        # --- Step 1: Match to Capital Calls ---
        # Find pending calls for this investor in this fund
        pending_calls = CapitalCall.objects.filter(
            fund=receipt.fund,
            investor=receipt.investor,
            # Assuming you add an 'is_fully_paid' flag or calculate distinct sum
        ).order_by('call_date')

        amount_remaining = receipt.amount_received
        
        # In a real implementation, you would link the Receipt to the Call 
        # via a ManyToMany or a 'Allocation' model. 
        # For now, we logically assume FIFO clearance of dues.
        
        # --- Step 2: Issue Units ---
        # Strategy A: Fixed Unit Price (Standard AIF)
        # Strategy B: NAV Based (Hedge Fund / Cat III)
        
        # Let's attempt to find the latest NAV to determine unit price
        latest_nav = NavSnapshot.objects.filter(
            fund=receipt.fund
        ).order_by('-as_on_date').first()
        
        # Default to Par Value (Face Value) if no NAV exists (Day 1)
        issue_price = latest_nav.nav_per_unit if latest_nav else Decimal('100.00') # Default Face Value
        
        if issue_price <= 0:
            raise ValueError("Issue Price (NAV) cannot be zero or negative.")

        units_to_issue = receipt.amount_received / issue_price

        # Check for Partly Paid logic
        # If the fund scheme is 'Partly Paid', we might update existing units instead.
        # For this example, we assume standard 'Issue New Units' model.
        
        InvestorUnitIssue.objects.create(
            fund=receipt.fund,
            investor=receipt.investor,
            units_issued=units_to_issue,
            nav_at_issue=issue_price,
            amount_paid_per_unit=issue_price, # Fully paid issuance
            is_partly_paid=False,
            transaction_currency=receipt.transaction_currency,
            exchange_rate=receipt.exchange_rate,
            notes=f"Auto-issued from Receipt #{receipt.id}"
        )

    @staticmethod
    def get_outstanding_capital_calls(fund, investor):
        """
        Calculates how much money is 'Due' from an investor.
        Total Called - Total Received.
        """
        total_called = CapitalCall.objects.filter(
            fund=fund, investor=investor
        ).aggregate(sum=models.Sum('amount_called'))['sum'] or 0
        
        total_received = DrawdownReceipt.objects.filter(
            fund=fund, investor=investor
        ).aggregate(sum=models.Sum('amount_received'))['sum'] or 0
        
        return max(0, total_called - total_received)