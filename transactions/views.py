from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, F
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Models & Forms
from .models import (
    CapitalCall, DrawdownReceipt, PurchaseTransaction, 
    RedemptionTransaction, Distribution, InvestorCommitment, InvestorUnitIssue
)
from .forms import (
    CapitalCallForm, DrawdownReceiptForm, PurchaseTransactionForm, 
    RedemptionForm, DistributionForm, InvestorCommitmentForm
)
from .utils import calculate_fifo_gain

from .serializers import (
    CapitalCallSerializer, DrawdownReceiptSerializer, PurchaseSerializer, 
    RedemptionSerializer, DistributionSerializer, InvestorCommitmentSerializer, InvestorUnitIssueSerializer
)

from investors.models import Investor
from funds.models import Fund


# Services
from .services import TransactionService

# ==========================================
# 1. API ViewSets (DRF)
# ==========================================

class InvestorCommitmentViewSet(viewsets.ModelViewSet):
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


# ==========================================
# 2. OPERATIONAL DASHBOARDS
# ==========================================

@login_required
def transaction_dashboard(request):
    """
    Operational view showing pending collections and fund health.
    """
    # 1. Outstanding Capital Calls (Filter for unpaid/partially paid)
    outstanding_calls = CapitalCall.objects.filter(
        is_fully_paid=False
    ).select_related('investor', 'fund').order_by('due_date')

    # 2. Financial Aggregates
    total_committed = InvestorCommitment.objects.aggregate(Sum('amount_committed'))['amount_committed__sum'] or 0
    total_drawn = CapitalCall.objects.aggregate(Sum('amount_called'))['amount_called__sum'] or 0
    
    # Calculate outstanding dues value
    outstanding_amount = outstanding_calls.aggregate(Sum('amount_called'))['amount_called__sum'] or 0

    context = {
        'outstanding_calls': outstanding_calls,
        'total_committed': total_committed,
        'total_drawn': total_drawn,
        'outstanding_amount': outstanding_amount,
        'percent_drawn': (total_drawn / total_committed * 100) if total_committed > 0 else 0
    }
    # Note: Using lowercase 'transactions_dashboard.html' to keep project consistent
    return render(request, 'transactions/transactions_dashboard.html', context)

@login_required
def transaction_list(request):
    """
    The 'Master Ledger' view.
    """
    return render(request, 'transactions/transactions_list.html', {
        'commitments': InvestorCommitment.objects.all().select_related('investor', 'fund').order_by('-commitment_date'),
        'calls': CapitalCall.objects.all().select_related('investor', 'fund').order_by('-call_date'),
        'receipts': DrawdownReceipt.objects.all().select_related('investor', 'fund').order_by('-date_received'),
        'investments': PurchaseTransaction.objects.all().order_by('-transaction_date'),
        'redemptions': RedemptionTransaction.objects.all().order_by('-transaction_date'),
        'distributions': Distribution.objects.all().order_by('-distribution_date')
    })


# ==========================================
# 3. TRANSACTION ACTION VIEWS
# ==========================================

@login_required
def create_commitment(request):

    investor_id = request.GET.get('investor')
    initial_data = {}
    if investor_id:
        initial_data['investor'] = get_object_or_404(Investor, id=investor_id)

    form = InvestorCommitmentForm(request.POST or None, initial=initial_data)
    
    if request.method == 'POST' and form.is_valid():
        commitment = form.save()
        messages.success(request, f"Successfully subscribed {commitment.investor.name} to {commitment.fund.name}")
        
        # IMPROVEMENT: Redirect back to the Investor Detail page instead of the general list
        return redirect('investors:portal-detail', pk=commitment.investor.pk)
        
    return render(request, 'transactions/form_entry.html', {
        'form': form, 
        'title': 'New Fund Subscription'
    })

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
    """
    Records a payment receipt and triggers the Service to issue units.
    """
    call_id = request.GET.get('call')
    initial_data = {}
    
    if call_id:
        call = get_object_or_404(CapitalCall, id=call_id)
        initial_data = {
            'fund': call.fund,
            'investor': call.investor,
            'amount_received': call.amount_called,
            'capital_call': call,
        }

    form = DrawdownReceiptForm(request.POST or None, initial=initial_data)
    
    if request.method == 'POST' and form.is_valid():
        receipt = form.save()
        
        # ATOMIC ACTION: Process units and update call status
        try:
            TransactionService.process_receipt(receipt.id)
            messages.success(request, f"Receipt recorded & Units issued to {receipt.investor.name}")
        except Exception as e:
            messages.error(request, f"Receipt saved, but unit issuance failed: {str(e)}")
            
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
        
        # FIFO Gain Calculation
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

@login_required
def portfolio_summary(request, fund_id):
    fund = get_object_or_404(Fund, id=fund_id)
    holdings = PortfolioService.get_fund_holdings(fund)
    
    # Add 'current_value' logic if you have a MarketPrice model
    # For now, we show Cost Basis
    return render(request, 'transactions/portfolio_summary.html', {
        'fund': fund,
        'holdings': holdings,
    })