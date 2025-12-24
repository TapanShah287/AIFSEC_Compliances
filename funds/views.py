from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
import json

# DRF Imports for API
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Local Models & Serializers
from .models import Fund, StewardshipEngagement, NavSnapshot
from .forms import FundForm, StewardshipEngagementForm, NavSnapshotForm
from .serializers import FundSerializer

# FIXED IMPORT: Now pointing to analytics.py to avoid conflict with services/ folder
from .analytics import FundAnalyticsService

# Transaction Dependencies (For wrapper views)
from transactions.forms import (
    InvestorCommitmentForm, CapitalCallForm, 
    DrawdownReceiptForm, DistributionForm
)
from transactions.models import PurchaseTransaction

# =========================================================
#  API VIEWSETS (Used by api/urls.py)
# =========================================================

class FundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Funds to be viewed or edited.
    """
    queryset = Fund.objects.all().order_by('-date_of_inception')
    serializer_class = FundSerializer
    permission_classes = [IsAuthenticated]

# =========================================================
#  CORE FUND MANAGEMENT
# =========================================================

@login_required
def portal_funds_list(request):
    funds = Fund.objects.all().order_by('-date_of_inception')
    # Simple summary stats per fund
    for f in funds:
        f.stats_committed = f.total_commitments
        
    return render(request, "funds/funds_list.html", {"funds": funds})

@login_required
def fund_add(request):
    if request.method == "POST":
        form = FundForm(request.POST)
        if form.is_valid():
            fund = form.save()
            messages.success(request, f"Fund '{fund.name}' initialized successfully.")
            return redirect('funds:fund_detail', pk=fund.pk)
    else:
        form = FundForm()
    return render(request, "funds/fund_add.html", {"form": form})

@login_required
def fund_detail(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    
    # Initialize the renamed service
    analytics = FundAnalyticsService(fund)
    
    # 1. Fetch Analytics
    summary = analytics.get_fund_summary()
    
    # 2. Compliance Alerts Logic (Mock for now)
    alerts = []
    if fund.jurisdiction == 'IFSC' and not fund.stewardship_logs.exists():
        alerts.append({'level': 'warning', 'message': 'IFSCA Mandatory: No Stewardship engagements logged yet.'})
    
    return render(request, "funds/fund_detail.html", {
        "fund": fund,
        "summary": summary,
        "compliance_alerts": alerts
    })

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
    return render(request, "transactions/add_commitment.html", {"fund": fund, "form": form})

@login_required
def create_capital_call(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    if request.method == "POST":
        form = CapitalCallForm(request.POST, fund_context=fund)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.fund = fund
            obj.save()
            messages.success(request, "Capital Call created.")
            return redirect('funds:fund_detail', pk=fund.pk)
    else:
        form = CapitalCallForm(fund_context=fund)
    return render(request, "transactions/create_call.html", {"fund": fund, "form": form})

@login_required
def add_receipt(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    if request.method == "POST":
        form = DrawdownReceiptForm(request.POST, fund_context=fund)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.fund = fund
            obj.save()
            messages.success(request, "Receipt recorded.")
            return redirect('funds:fund_detail', pk=fund.pk)
    else:
        form = DrawdownReceiptForm(fund_context=fund)
    return render(request, "transactions/add_receipt.html", {"fund": fund, "form": form})

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