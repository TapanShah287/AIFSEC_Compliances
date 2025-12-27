from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from django.utils.text import slugify

import json
from django.db.models import F

# DRF Imports for API
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Local Models & Serializers
from .models import Fund, StewardshipEngagement, NavSnapshot
from manager_entities.models import ManagerEntity
from .forms import FundForm, StewardshipEngagementForm, NavSnapshotForm
from transactions.forms import DrawdownReceiptForm, DistributionForm, InvestorCommitmentForm, CapitalCallForm
from .serializers import FundSerializer

# FIXED IMPORT: Now pointing to analytics.py to avoid conflict with services/ folder
from .analytics import FundAnalyticsService

# Transaction Dependencies (For wrapper views)
from transactions.models import PurchaseTransaction

# =========================================================
#  API VIEWSETS (Used by api/urls.py)
# =========================================================

class FundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Funds to be viewed or edited.
    """
    serializer_class = FundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        manager_entity = get_current_manager_entity(self.request)
        return Fund.objects.filter(
            manager_entity=manager_entity
        ).order_by('-date_of_inception')
# =========================================================

def get_current_manager_entity(request):
    """
    Retrieves the Manager Entity currently active in the user's session.
    """
    active_id = request.session.get('active_entity_id')
    if active_id:
        return ManagerEntity.objects.filter(id=active_id).first()
    
    # Fallback to the first associated entity if session is empty
    first_membership = request.user.memberships.first()
    if first_membership:
        request.session['active_entity_id'] = first_membership.entity.id
        return first_membership.entity
    return None

# =========================================================
#  CORE FUND MANAGEMENT
# =========================================================

@login_required
def calculate_nav_view(request, pk):
    """
    The NAV Computation Workspace.
    Calculates Assets - Liabilities to derive Per Unit Value.
    """
    from transactions.models import PurchaseTransaction, DrawdownReceipt, Distribution

    fund = get_object_or_404(Fund, pk=pk)
    
    # 1. Asset Side: Portfolio Fair Value
    # In a real app, this pulls from the latest ShareValuation of investee companies
    portfolio_value = PurchaseTransaction.objects.filter(fund=fund).aggregate(
        total=Sum(F('quantity') * F('exchange_rate')) # Simplified logic
    )['total'] or Decimal('0.00')

    # 2. Asset Side: Cash Balance
    total_inflow = DrawdownReceipt.objects.filter(capital_call__fund=fund).aggregate(Sum('amount_received'))['amount_received__sum'] or 0
    total_outflow = Distribution.objects.filter(fund=fund).aggregate(Sum('gross_amount'))['gross_amount__sum'] or 0
    cash_balance = total_inflow - total_outflow - portfolio_value # Simplistic cash drag

    # 3. Units Outstanding
    total_units = fund.nav_snapshots.latest('as_on_date').units_outstanding if fund.nav_snapshots.exists() else Decimal('1.0')

    # 4. NAV Calculation
    net_assets = portfolio_value + cash_balance
    nav_per_unit = net_assets / total_units if total_units > 0 else 0

    context = {
        'fund': fund,
        'portfolio_value': portfolio_value,
        'cash_balance': cash_balance,
        'net_assets': net_assets,
        'total_units': total_units,
        'nav_per_unit': nav_per_unit,
    }
    return render(request, 'funds/nav_computation.html', context)

@login_required
def portal_funds_list(request):
    manager_entity = get_current_manager_entity(request)
    funds = Fund.objects.filter(
        manager_entity=manager_entity
    ).order_by('-date_of_inception')

    for f in funds:
        f.stats_committed = f.total_commitments

    return render(request, "funds/funds_list.html", {
        "funds": funds,
        "manager_entity": manager_entity,
    })

@login_required
def fund_add(request):
    """Workflow to launch a new fund."""
    manager_entity = get_current_manager_entity(request)

    if request.method == "POST":
        form = FundForm(request.POST)
        if form.is_valid():
            fund = form.save(commit=False)
            fund.manager_entity = manager_entity
            fund.slug = slugify(fund.name)
            fund.save()
            
            # NEW: Trigger the automation
            try:
                from compliances.services import generate_standard_aif_tasks
                task_count = generate_standard_aif_tasks(fund)
                messages.info(request, f"Generated {task_count} regulatory tasks for the new fund.")
            except Exception as e:
                print(f"Task generation failed: {e}")

            return render(request, "funds/fund_success.html", {"fund": fund})
    else:
        form = FundForm()

    return render(request, "funds/fund_add.html", {
        "form": form,
        "manager_entity": manager_entity,
        "title": "Launch New Fund"
    })

@login_required
def fund_detail(request, pk):
    """
    Comprehensive view for Fund Overview.
    Calculates Cap Table, Analytics Summary, and Upcoming Compliance.
    """
    fund = get_object_or_404(Fund, pk=pk)

    # 1. CAP TABLE CALCULATIONS
    # Fetch all holdings for this fund, optimized with select_related for investor names
    cap_table = fund.cap_table.all().select_related('investor').order_by('-total_units')
    
    # Calculate the total units across the whole fund for ownership % logic
    total_fund_units = cap_table.aggregate(total=Sum('total_units'))['total'] or Decimal('0.0000')

    # 2. ANALYTICS SERVICE
    # Initialize your analytics service to get called capital, DPI, etc.
    analytics = FundAnalyticsService(fund)
    summary = analytics.get_fund_summary()

    # 3. COMPLIANCE TASKS LOGIC
    upcoming_tasks = []
    try:
        # We import inside the function or locally to prevent circular dependencies
        from compliances.models import ComplianceTask
        today = timezone.now().date()
        
        # Filter for PENDING/IN_PROGRESS tasks linked to this specific fund
        upcoming_tasks = ComplianceTask.objects.filter(
            fund=fund,
            status__in=['PENDING', 'IN_PROGRESS']
        ).order_by('due_date')[:3]

        # Calculate "Days Remaining" or "Days Overdue" for the UI sidebar
        for task in upcoming_tasks:
            diff = (task.due_date - today).days
            task.days_left = diff
            # If diff is -2, it means 2 days overdue
            task.days_overdue = abs(diff) if diff < 0 else 0
            
    except (ImportError, Exception) as e:
        # Fallback if the compliance app isn't migrated or available
        print(f"Compliance fetch error: {e}")
        upcoming_tasks = []

    # 4. COMPLIANCE ALERTS (Business Logic)
    alerts = []
    # Example: IFSC Funds MUST have stewardship logs per 2024/25 regulations
    if fund.jurisdiction == 'IFSC' and not fund.stewardship_logs.exists():
        alerts.append({
            'level': 'warning', 
            'message': 'IFSCA Compliance: No Stewardship engagements logged for this fund.'
        })
    
    # Example: Low Commitment Alert
    if summary.get('commitment_percentage', 0) < 10:
        alerts.append({
            'level': 'info',
            'message': 'Fundraising: Commitment levels are currently below 10% of target corpus.'
        })

    # 5. CONTEXT PREPARATION
    context = {
        "fund": fund,
        "cap_table": cap_table,
        "total_fund_units": total_fund_units,
        "summary": summary,
        "compliance_alerts": alerts,
        "upcoming_tasks": upcoming_tasks
    }

    return render(request, "funds/fund_detail.html", context)

# =========================================================
#  PORTFOLIO & REPORTING
# =========================================================

@login_required
def fund_portfolio(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    # Note: If your valuation logic is in 'services/valuation_nav.py' (top level or funds level)
    # Ensure this import path matches your actual folder structure.
    # If it is in funds/services/valuation_nav.py, import as:
    # from .services.valuation_nav import get_fund_holdings
    try:
        from services.valuation_nav import get_fund_holdings
    except ImportError:
        # Fallback if user placed it inside funds/services/
        from .services.valuation_nav import get_fund_holdings

    holdings_dict = get_fund_holdings(fund)
    
    # Flatten for template
    holdings_list = []
    for key, data in holdings_dict.items():
        # Fetch company name
        from investee_companies.models import InvesteeCompany, ShareCapital
        comp = InvesteeCompany.objects.get(pk=data['company_id'])
        sc = ShareCapital.objects.get(pk=data['share_capital_id'])
        
        data['company_name'] = comp.name
        data['share_class'] = sc.class_name
        holdings_list.append(data)

    return render(request, "funds/fund_portfolio.html", {
        "fund": fund, 
        "holdings": holdings_list
    })

@login_required
def fund_performance(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    return render(request, "funds/performance_report.html", {"fund": fund})

@login_required
def activity_log(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    # Fetch all transactions unioned (simplified) or separate lists
    return render(request, "funds/activity_log.html", {"fund": fund})

# =========================================================
#  COMPLIANCE ACTIONS
# =========================================================

@login_required
def log_stewardship_engagement(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    if request.method == "POST":
        form = StewardshipEngagementForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.fund = fund
            obj.save()
            messages.success(request, "Stewardship engagement logged.")
            return redirect('funds:fund_detail', pk=fund.pk)
    else:
        form = StewardshipEngagementForm()
    return render(request, "funds/log_stewardship.html", {"fund": fund, "form": form})

@login_required
def migrate_to_ai_only(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    if request.method == "POST":
        # In real world: Validate consent docs
        fund.scheme_type = 'AI_ONLY'
        fund.save()
        messages.success(request, "Fund migrated to 'Accredited Investor Only' status.")
    return redirect('funds:fund_detail', pk=fund.pk)

# =========================================================
#  TRANSACTION WRAPPERS (For Convenience URLs)
# =========================================================

@login_required
def add_commitment(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    if request.method == "POST":
        form = InvestorCommitmentForm(request.POST, fund_context=fund)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.fund = fund
            obj.save()
            messages.success(request, "Investor onboarded successfully.")
            return redirect('funds:fund_detail', pk=fund.pk)
    else:
        form = InvestorCommitmentForm(fund_context=fund)
    return render(request, "funds/add_commitment.html", {"fund": fund, "form": form})

@login_required
def create_capital_call(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    
    if request.method == "POST":
        form = CapitalCallForm(request.POST, fund_context=fund) # Pass fund here
        if form.is_valid():
            call = form.save(commit=False)
            call.fund = fund # Ensure the call object is linked to the fund
            call.save()
            messages.success(request, "Capital call issued successfully.")
            return redirect('funds:fund_detail', pk=fund.pk)
    else:
        form = CapitalCallForm(fund_context=fund) # Pass fund here
        
    return render(request, "transactions/add_capitalcall.html", {"fund": fund, "form": form})

@login_required
def add_receipt(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    
    if request.method == 'POST':
        # Pass 'fund' as the first positional argument
        form = DrawdownReceiptForm(fund, request.POST) 
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.fund = fund
            receipt.save()
            messages.success(request, f"Units issued to {receipt.investor.name}")
            return redirect('funds:fund-detail', pk=fund.pk)
    else:
        # Pass 'fund' as the first positional argument here too
        # Change from (fund=fund) to just (fund)
        form = DrawdownReceiptForm(fund) 
    
    return render(request, 'transactions/add_receipt.html', {
        'form': form, 
        'fund': fund
    })

@login_required
def add_distribution(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    if request.method == "POST":
        form = DistributionForm(request.POST, fund_context=fund)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.fund = fund
            obj.save()
            messages.success(request, "Distribution recorded.")
            return redirect('funds:fund_detail', pk=fund.pk)
    else:
        form = DistributionForm(fund_context=fund)
    return render(request, "transactions/add_distribution.html", {"fund": fund, "form": form})