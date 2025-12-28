from decimal import Decimal
from django.db import transaction
from .models import CapitalCall, DrawdownReceipt, InvestorUnitIssue
from funds.models import NavSnapshot, InvestorPosition

class TransactionService:
    
    @staticmethod
    @transaction.atomic
    def process_receipt(receipt_id):
        """
        1. Fetch Receipt
        2. Find applicable NAV (Latest prior to receipt date)
        3. Issue Units
        4. Mark Capital Call as Paid
        """
        receipt = DrawdownReceipt.objects.get(id=receipt_id)
        
        # 1. FIND NAV (Critical Fix: Don't hardcode 10.00)
        try:
            latest_nav_obj = NavSnapshot.objects.filter(
                fund=receipt.fund,
                date__lte=receipt.receipt_date
            ).latest('date')
            current_nav = latest_nav_obj.nav_per_unit
        except NavSnapshot.DoesNotExist:
            # Fallback for Day 1
            current_nav = Decimal('10.00')

        # 2. CALCULATE UNITS
        units_to_issue = receipt.amount_received / current_nav

        # 3. UPDATE CAP TABLE (InvestorPosition)
        position, _ = InvestorPosition.objects.get_or_create(
            investor=receipt.investor,
            fund=receipt.fund
        )
        position.total_units += units_to_issue
        position.total_capital_contributed += receipt.amount_received
        position.save()

        # 4. LOG ISSUANCE
        InvestorUnitIssue.objects.create(
            fund=receipt.fund,
            investor=receipt.investor,
            units_issued=units_to_issue,
            nav_at_issue=current_nav,
            amount_paid_per_unit=current_nav,
            transaction_currency=receipt.transaction_currency
        )
        
        # 5. UPDATE CALL STATUS
        if receipt.capital_call:
            # Check if fully paid
            total_paid = receipt.capital_call.receipts.aggregate(
                models.Sum('amount_received')
            )['amount_received__sum'] or 0
            
            if total_paid >= receipt.capital_call.amount_called:
                receipt.capital_call.is_fully_paid = True
                receipt.capital_call.save()

class PortfolioService:
    @staticmethod
    def get_fund_holdings(fund):
        """
        Calculates the current quantity and cost of all stocks held by a Fund.
        """
        from .models import PurchaseTransaction, RedemptionTransaction
        
        holdings = []
        # Get unique companies the fund has invested in
        companies = PurchaseTransaction.objects.filter(fund=fund).values_list('investee_company', flat=True).distinct()
        
        for company_id in companies:
            # 1. Calculate Total Quantity Held
            total_purchased = PurchaseTransaction.objects.filter(
                fund=fund, investee_company_id=company_id
            ).aggregate(Sum('quantity'))['quantity__sum'] or Decimal('0')
            
            total_sold = RedemptionTransaction.objects.filter(
                fund=fund, investee_company_id=company_id
            ).aggregate(Sum('quantity'))['quantity__sum'] or Decimal('0')
            
            current_qty = total_purchased - total_sold
            
            if current_qty > 0:
                # 2. Calculate Weighted Average Cost
                total_cost = PurchaseTransaction.objects.filter(
                    fund=fund, investee_company_id=company_id
                ).aggregate(total=Sum(F('quantity') * F('price_per_share')))['total'] or Decimal('0')
                
                avg_cost = total_cost / total_purchased if total_purchased > 0 else 0
                
                holdings.append({
                    'company_id': company_id,
                    'quantity': current_qty,
                    'avg_cost': avg_cost,
                    'total_cost': current_qty * avg_cost,
                })
        return holdings