from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from decimal import Decimal

# App Model Imports
from funds.models import Fund
from investors.models import Investor
from investee_companies.models import InvesteeCompany
from transactions.models import (
    DrawdownReceipt, 
    PurchaseTransaction, 
    RedemptionTransaction, 
    Distribution
)
from compliances.models import ComplianceTask

@login_required
def dashboard_view(request):
    """
    Main System Overview Dashboard.
    Aggregates operational counts and global financial metrics across all funds.
    Supports dynamic scaling for Crores (10^7) or Millions (10^6).
    """
    # 1. Operational Counts
    fund_count = Fund.objects.count()
    investor_count = Investor.objects.count()
    company_count = InvesteeCompany.objects.count()

    # 2. Global Financial Aggregations (Raw Data)
    total_drawdowns = DrawdownReceipt.objects.aggregate(s=Sum('amount_received'))['s'] or 0
    total_investments = PurchaseTransaction.objects.aggregate(
        total=Sum(ExpressionWrapper(F('quantity') * F('price_per_share'), output_field=DecimalField()))
    )['total'] or 0
    total_redemptions = RedemptionTransaction.objects.aggregate(
        total=Sum(ExpressionWrapper(F('quantity') * F('price_per_share'), output_field=DecimalField()))
    )['total'] or 0
    total_distributions = Distribution.objects.aggregate(s=Sum('gross_amount'))['s'] or 0

    cash_available = (total_drawdowns + total_redemptions) - (total_investments + total_distributions)

    # 3. Denomination / Scaling Logic
    denom = request.GET.get('denom', 'cr') # Default to Crores for Indian AIF context
    
    if denom == 'm':
        divisor = Decimal('1000000')
        suffix = "M"
    elif denom == 'raw':
        divisor = Decimal('1')
        suffix = ""
    else:
        divisor = Decimal('10000000') # 1 Crore = 10^7
        suffix = "Cr"

    def scale(value):
        """Helper to divide by denomination and format to 2 decimals."""
        try:
            return (Decimal(value) / divisor).quantize(Decimal('0.01'))
        except:
            return Decimal('0.00')

    # 4. Compliance Stats
    overdue_count = ComplianceTask.objects.filter(status='OVERDUE').count()

    context = {
        "fund_count": fund_count,
        "investor_count": investor_count,
        "company_count": company_count,
        "overdue_count": overdue_count,
        "denom": denom,
        "suffix": suffix,
        "stats": {
            "total_drawdowns": scale(total_drawdowns),
            "total_investments": scale(total_investments),
            "total_redemptions": scale(total_redemptions),
            "total_distributions": scale(total_distributions),
            "cash_available": scale(cash_available),
        }
    }

    return render(request, "dashboard/dashboard.html", context)