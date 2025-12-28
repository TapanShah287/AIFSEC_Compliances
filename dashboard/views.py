from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from decimal import Decimal
from django.utils import timezone

# Model Imports
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
    # 1. Operational Counts
    fund_count = Fund.objects.count()
    investor_count = Investor.objects.count()
    company_count = InvesteeCompany.objects.count()

    # 2. Global Financial Aggregations
    total_drawdowns = DrawdownReceipt.objects.aggregate(s=Sum('amount_received'))['s'] or 0
    total_investments = PurchaseTransaction.objects.aggregate(
        total=Sum(ExpressionWrapper(F('quantity') * F('price_per_share'), output_field=DecimalField()))
    )['total'] or 0
    total_redemptions = RedemptionTransaction.objects.aggregate(
        total=Sum(ExpressionWrapper(F('quantity') * F('price_per_share'), output_field=DecimalField()))
    )['total'] or 0
    total_distributions = Distribution.objects.aggregate(s=Sum('gross_amount'))['s'] or 0

    cash_available = (total_drawdowns + total_redemptions) - (total_investments + total_distributions)

    # 3. Denomination Scaling Logic
    denom = request.GET.get('denom', 'cr')
    if denom == 'm':
        divisor, suffix = Decimal('1000000'), "M"
    elif denom == 'raw':
        divisor, suffix = Decimal('1'), ""
    else:
        divisor, suffix = Decimal('10000000'), "Cr"

    def scale(value):
        try:
            return (Decimal(value) / divisor).quantize(Decimal('0.01'))
        except:
            return Decimal('0.00')

    # 4. Activity & Compliance Feeds (NEW: Required by your HTML)
    # Feed 1: Recent Cash Inflow
    recent_activities = DrawdownReceipt.objects.select_related('investor', 'fund').order_by('-date_received')[:5]

    # Feed 2: Upcoming Deadlines
    upcoming_filings = ComplianceTask.objects.filter(
        status__in=['PENDING', 'IN_PROGRESS'],
        due_date__gte=timezone.now().date()
    ).select_related('fund').order_by('due_date')[:4]

    # Feed 3: Overdue Count
    overdue_count = ComplianceTask.objects.filter(status='OVERDUE').count()

    context = {
        "fund_count": fund_count,
        "investor_count": investor_count,
        "company_count": company_count,
        "overdue_count": overdue_count,
        "recent_activities": recent_activities,    # Added for Activity section
        "upcoming_filings": upcoming_filings,      # Added for Compliance Watch
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