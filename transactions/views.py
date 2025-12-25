from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import CapitalCall, DrawdownReceipt, PurchaseTransaction, RedemptionTransaction, Distribution, InvestorCommitment, InvestorUnitIssue
from .forms import CapitalCallForm, DrawdownReceiptForm, PurchaseTransactionForm, RedemptionForm, DistributionForm, InvestorCommitmentForm

from .serializers import (
    InvestorCommitmentSerializer, CapitalCallSerializer, 
    PurchaseSerializer, RedemptionSerializer, 
    DrawdownReceiptSerializer, InvestorUnitIssueSerializer,
    DistributionSerializer
)

from .utils import calculate_fifo_gain

class InvestorCommitmentViewSet(viewsets.ModelViewSet):
    """FIXED: Matches the name expected by api/urls.py"""
    queryset = InvestorCommitment.objects.all()
    serializer_class = InvestorCommitmentSerializer
    permission_classes = [IsAuthenticated]

class CapitalCallViewSet(viewsets.ModelViewSet):
    queryset = CapitalCall.objects.all()
    serializer_class = CapitalCallSerializer
    permission_classes = [IsAuthenticated]

class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = PurchaseTransaction.objects.all()
    serializer_class = PurchaseSerializer
    permission_classes = [IsAuthenticated]

class RedemptionViewSet(viewsets.ModelViewSet):
    queryset = RedemptionTransaction.objects.all()
    serializer_class = RedemptionSerializer
    permission_classes = [IsAuthenticated]

class DrawdownReceiptViewSet(viewsets.ModelViewSet):
    queryset = DrawdownReceipt.objects.all()
    serializer_class = DrawdownReceiptSerializer
    permission_classes = [IsAuthenticated]

class InvestorUnitIssueViewSet(viewsets.ModelViewSet):
    queryset = InvestorUnitIssue.objects.all()
    serializer_class = InvestorUnitIssueSerializer
    permission_classes = [IsAuthenticated]

class DistributionViewSet(viewsets.ModelViewSet):
    queryset = Distribution.objects.all()
    serializer_class = DistributionSerializer
    permission_classes = [IsAuthenticated]


@login_required
def transaction_list(request):
    return render(request, 'transactions/transactions_list.html', {
        'commitments': InvestorCommitment.objects.all().order_by('-commitment_date'),
        'calls': CapitalCall.objects.all().order_by('-call_date'),
        'receipts': DrawdownReceipt.objects.all().order_by('-received_date'),
        'investments': PurchaseTransaction.objects.all().order_by('-transaction_date'),
        'redemptions': RedemptionTransaction.objects.all().order_by('-transaction_date'),
        'distributions': Distribution.objects.all().order_by('-distribution_date')
    })

# --- CREATE VIEWS ---

@login_required
def create_commitment(request):
    form = InvestorCommitmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Investor Commitment recorded.")
        return redirect('portal-transactions')
    return render(request, 'transactions/form_entry.html', {'form': form, 'title': 'New Commitment'})

@login_required
def create_capital_call(request):
    form = CapitalCallForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Capital Call recorded.")
        return redirect('portal-transactions')
    return render(request, 'transactions/form_entry.html', {'form': form, 'title': 'New Capital Call'})

@login_required
def create_receipt(request):
    form = DrawdownReceiptForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        receipt = form.save()
        # Auto-Close Logic
        call = receipt.capital_call
        paid = call.receipts.aggregate(Sum('amount_received'))['amount_received__sum'] or 0
        if paid >= call.amount_called:
            call.is_paid = True
            call.save()
        messages.success(request, "Receipt recorded.")
        return redirect('portal-transactions')
    return render(request, 'transactions/form_entry.html', {'form': form, 'title': 'Record Payment Receipt'})

@login_required
def create_investment(request):
    form = PurchaseTransactionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Investment (Outflow) recorded.")
        return redirect('portal-transactions')
    return render(request, 'transactions/form_entry.html', {'form': form, 'title': 'Record Investment (Buy)'})

@login_required
def create_redemption(request):
    form = RedemptionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        redemption = form.save(commit=False)
        redemption.save()
        # Run FIFO Engine
        cost, gain = calculate_fifo_gain(redemption)
        redemption.cost_basis = cost
        redemption.realized_gain = gain
        redemption.save()
        messages.success(request, f"Redemption recorded. Realized Gain: {gain}")
        return redirect('portal-transactions')
    return render(request, 'transactions/form_entry.html', {'form': form, 'title': 'Record Redemption (Sell)'})

@login_required
def create_distribution(request):
    form = DistributionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Distribution recorded.")
        return redirect('portal-transactions')
    return render(request, 'transactions/form_entry.html', {'form': form, 'title': 'Record Distribution'})