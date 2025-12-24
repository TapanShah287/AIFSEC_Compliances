from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from decimal import Decimal

# Model Imports
from funds.models import Fund
from .models import (
    PurchaseTransaction, RedemptionTransaction,
    InvestorCommitment, CapitalCall, DrawdownReceipt, 
    Distribution, InvestorUnitIssue
)

# Serializer Imports
from .serializers import (
    PurchaseSerializer, RedemptionSerializer,
    InvestorCommitmentSerializer, CapitalCallSerializer, 
    DrawdownReceiptSerializer, DistributionSerializer,
    InvestorUnitIssueSerializer
)

# Form Imports
from .forms import PurchaseForm, RedemptionForm

# =========================================================
#  API VIEWSETS (Data for Dashboard/Ledger)
# =========================================================

class BaseTransactionViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for all transaction types.
    Provides common permission, filter, and ordering configurations.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['fund', 'transaction_currency']
    ordering_fields = '__all__'

class PurchaseViewSet(BaseTransactionViewSet):
    """ViewSet for Investment trades."""
    queryset = PurchaseTransaction.objects.all().select_related(
        'investee_company', 'fund', 'transaction_currency', 'share_capital'
    )
    serializer_class = PurchaseSerializer
    filterset_fields = ['fund', 'investee_company', 'transaction_currency']

class RedemptionViewSet(BaseTransactionViewSet):
    """ViewSet for Exit trades."""
    queryset = RedemptionTransaction.objects.all().select_related(
        'investee_company', 'fund', 'transaction_currency', 'share_capital'
    )
    serializer_class = RedemptionSerializer
    filterset_fields = ['fund', 'investee_company', 'transaction_currency']

class InvestorCommitmentViewSet(BaseTransactionViewSet):
    """ViewSet for LP Commitments."""
    queryset = InvestorCommitment.objects.all().select_related(
        'investor', 'fund', 'transaction_currency'
    )
    serializer_class = InvestorCommitmentSerializer
    filterset_fields = ['fund', 'investor', 'transaction_currency']

class CapitalCallViewSet(BaseTransactionViewSet):
    """ViewSet for Drawdown requests."""
    queryset = CapitalCall.objects.all().select_related(
        'investor', 'fund', 'transaction_currency'
    )
    serializer_class = CapitalCallSerializer
    filterset_fields = ['fund', 'investor']

class DrawdownReceiptViewSet(BaseTransactionViewSet):
    """ViewSet for Capital receipts."""
    queryset = DrawdownReceipt.objects.all().select_related(
        'investor', 'fund', 'transaction_currency', 'capital_call'
    )
    serializer_class = DrawdownReceiptSerializer
    filterset_fields = ['fund', 'investor', 'capital_call']

class DistributionViewSet(BaseTransactionViewSet):
    """ViewSet for LP Distributions."""
    queryset = Distribution.objects.all().select_related(
        'investor', 'fund', 'transaction_currency'
    )
    serializer_class = DistributionSerializer
    filterset_fields = ['fund', 'investor']

class InvestorUnitIssueViewSet(BaseTransactionViewSet):
    """ViewSet for SEBI 2025 Unit Allotments."""
    queryset = InvestorUnitIssue.objects.all().select_related(
        'investor', 'fund', 'transaction_currency'
    )
    serializer_class = InvestorUnitIssueSerializer
    filterset_fields = ['fund', 'investor', 'is_demat']

# =========================================================
#  PORTAL VIEWS (HTML Forms)
# =========================================================

@login_required
def portal_transactions_ledger(request):
    """Unified transaction ledger page showing recent activities."""
    return render(request, "portal/transactions.html", {
        "title": "Unified Transaction Ledger"
    })

@login_required
def add_purchase(request, fund_pk):
    """
    Record a new investment (Purchase).
    Ensures Multi-Currency data and Investee Cap Table updates are handled.
    """
    fund = get_object_or_404(Fund, pk=fund_pk)
    if request.method == "POST":
        # Pass fund_context to ensure form handles currency rates and shareholding updates
        form = PurchaseForm(request.POST, fund_context=fund)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.fund = fund
            # Save triggers multi-currency calculation and shareholding update (via form save override)
            txn.save() 
            messages.success(request, f"Successfully recorded purchase of {txn.quantity} units in {txn.investee_company.name}.")
            return redirect('funds:fund_portfolio', pk=fund.pk)
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = PurchaseForm(fund_context=fund)
    
    return render(request, "transactions/add_purchase.html", {
        "fund": fund,
        "form": form,
        "title": "Record Investment (Purchase)"
    })

@login_required
def add_redemption(request, fund_pk):
    """
    Record a sale/exit (Redemption).
    Handles FIFO cost basis tracking and Cap Table reduction.
    """
    fund = get_object_or_404(Fund, pk=fund_pk)
    if request.method == "POST":
        form = RedemptionForm(request.POST, fund_context=fund)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.fund = fund
            # Save triggers multi-currency and gain/loss calculations
            txn.save() 
            messages.success(request, f"Successfully recorded exit from {txn.investee_company.name}.")
            return redirect('funds:fund_portfolio', pk=fund.pk)
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = RedemptionForm(fund_context=fund)
    
    return render(request, "transactions/add_redemption.html", {
        "fund": fund,
        "form": form,
        "title": "Record Exit (Redemption)"
    })