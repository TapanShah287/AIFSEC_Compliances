from decimal import Decimal
from django.db.models import Sum
from transactions.models import CapitalCall, Distribution, InvestorCommitment

class FundAnalyticsService:
    """
    Centralizes logic for Fund Performance, NAV verification, and 
    Portfolio aggregation to keep views.py clean.
    """

    def __init__(self, fund):
        self.fund = fund

    def get_fund_summary(self):
        """
        Returns the core header stats for the Fund Dashboard.
        """
        # Aggregate logic
        total_committed = InvestorCommitment.objects.filter(fund=self.fund).aggregate(
            total=Sum('amount_committed')
        )['total'] or Decimal('0.00')

        total_called = CapitalCall.objects.filter(fund=self.fund).aggregate(
            total=Sum('amount_called')
        )['total'] or Decimal('0.00')

        total_distributed = Distribution.objects.filter(fund=self.fund).aggregate(
            total=Sum('gross_amount')
        )['total'] or Decimal('0.00')

        # Basic Checks
        percent_called = (total_called / total_committed * 100) if total_committed > 0 else 0
        
        # DPI (Distributions to Paid-In Capital)
        dpi = (total_distributed / total_called) if total_called > 0 else 0
        
        # Safe access to currency symbol, fallback to code if symbol missing
        currency_symbol = getattr(self.fund.currency, 'symbol', self.fund.currency.code)

        return {
            "corpus": self.fund.corpus, # Target Corpus
            "total_committed": total_committed,
            "total_called": total_called,
            "total_distributed": total_distributed,
            "percent_called": round(percent_called, 2),
            "dpi": round(dpi, 2),
            "currency_symbol": currency_symbol
        }