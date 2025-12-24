from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from datetime import date
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import generics

# Local Imports
from .models import Investor, InvestorDocument
from .forms import InvestorForm, InvestorDocumentForm
from .serializers import InvestorSerializer

# Transaction Model Imports
from transactions.models import (
    InvestorCommitment, 
    CapitalCall, 
    DrawdownReceipt, 
    Distribution
)
# ==========================================
# 1. API ViewSets (Used by api/urls.py)
# ==========================================

class InvestorViewSet(viewsets.ModelViewSet):
    queryset = Investor.objects.all().order_by('name')
    serializer_class = InvestorSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'email', 'pan']

    @action(detail=True, methods=['get'])
    def portfolio(self, request, pk=None):
        """
        Custom endpoint to get a summary of this investor's portfolio.
        """
        investor = self.get_object()
        # Safe imports
        from transactions.models import InvestorCommitment, PurchaseTransaction
        
        commitments = InvestorCommitment.objects.filter(investor=investor).values(
            'fund__name', 'amount_committed'
        )
        
        return Response({
            "investor": investor.name,
            "commitments": list(commitments),
            "total_committed": investor.total_committed
        })

class InvestorKYCView(generics.RetrieveUpdateAPIView):
    """
    Dedicated endpoint for managing KYC status (api/investors/<id>/kyc/)
    """
    queryset = Investor.objects.all()
    serializer_class = InvestorSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        # You could trigger an email here
        serializer.save()

# ==========================================
# 2. Portal Views (HTML Templates)
# ==========================================

@login_required
def portal_investor_list(request):
    """
    Registry view with support for Denomination Scaling (INR/Cr/M).
    FIXED: Uses a wrapped data structure to ensure template compatibility.
    """
    investors_queryset = Investor.objects.all().order_by('name')
    
    # Scale Logic
    denom = request.GET.get('denom', 'raw')
    scale = Decimal('1')
    suffix = ""
    if denom == 'cr':
        scale = Decimal('10000000')
        suffix = "Cr"
    elif denom == 'm':
        scale = Decimal('1000000')
        suffix = "M"

    investors_data = []
    for investor in investors_queryset:
        # Calculate financial summary for the registry row
        committed = InvestorCommitment.objects.filter(investor=investor).aggregate(
            total=Sum('amount_committed'))['total'] or Decimal('0.00')
        
        contributed = DrawdownReceipt.objects.filter(investor=investor).aggregate(
            total=Sum('amount_received'))['total'] or Decimal('0.00')

        investors_data.append({
            'investor': investor, # Accessible in template as item.investor.name
            'total_committed': committed / scale,
            'uncalled_capital': (committed - contributed) / scale,
            'kyc_status': investor.kyc_status,
        })

    return render(request, 'investors/investor_list.html', {
        'investors': investors_data,
        'denom': denom,
        'suffix': suffix
    })

@login_required
def portal_investor_detail(request, pk):
    """
    Detailed dashboard for a single investor.
    Shows cross-fund commitments, uncalled capital, and document vault.
    """
    investor = get_object_or_404(Investor, pk=pk)
    
    # 1. Fetch Commitments
    commitments = InvestorCommitment.objects.filter(investor=investor).select_related('fund')
    
    # 2. Financial Summary
    # total_committed and total_contributed are handled by model properties
    total_committed = investor.total_committed
    total_contributed = investor.total_contributed
    
    # Aggregating Distributions (Returns)
    total_distributed = Distribution.objects.filter(investor=investor).aggregate(
        total=Sum('gross_amount')
    )['total'] or Decimal('0.00')
    
    uncalled_capital = total_committed - total_contributed

    # 3. 2025 COMPLIANCE ALERTS ENGINE
    compliance_alerts = []
    
    # Accreditation Check (Mandatory for AI-Only schemes)
    if investor.accreditation_status == 'EXPIRED' or (investor.accreditation_expiry and investor.accreditation_expiry < date.today()):
        compliance_alerts.append({
            'level': 'danger',
            'message': 'Accreditation certificate has expired. Mandatory update required for AI-only schemes.'
        })
    
    # Demat Mandate Check (SEBI 2025 Requirement)
    if not investor.demat_account_no:
        compliance_alerts.append({
            'level': 'warning',
            'message': 'Demat details missing. Unit allotment will fail for new SEBI AIF mandates post-July 2025.'
        })

    # 4. Documents Vault
    documents = investor.documents.all().order_by('-uploaded_at')

    context = {
        'investor': investor,
        'commitments': commitments,
        'total_committed': total_committed,
        'total_contributed': total_contributed,
        'total_distributed': total_distributed,
        'uncalled_capital': uncalled_capital,
        'documents': documents,
        'compliance_alerts': compliance_alerts,
    }
    return render(request, 'investors/investor_detail.html', context)

@login_required
def portal_investor_add(request):
    """Register a new investor with 2025 compliance details."""
    if request.method == "POST":
        form = InvestorForm(request.POST)
        if form.is_valid():
            investor = form.save()
            messages.success(request, f"Investor '{investor.name}' registered. Please upload KYC documents.")
            return redirect('investors:portal-detail', pk=investor.pk)
    else:
        form = InvestorForm()
    
    return render(request, 'investors/investor_add.html', {'form': form})

@login_required
def add_commitment(request, pk):
    """
    View to record a new capital commitment for a specific investor.
    Includes a local dynamic form for rapid entry.
    """
    investor = get_object_or_404(Investor, pk=pk)
    from django import forms
    
    INPUT_WIDGET_STYLE = 'w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500/10 transition-all'

    class CommitmentForm(forms.ModelForm):
        class Meta:
            model = InvestorCommitment
            fields = ['fund', 'amount_committed', 'commitment_date']
            widgets = {
                'fund': forms.Select(attrs={'class': INPUT_WIDGET_STYLE}),
                'amount_committed': forms.NumberInput(attrs={'class': INPUT_WIDGET_STYLE, 'placeholder': '0.00'}),
                'commitment_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_WIDGET_STYLE}),
            }

    if request.method == "POST":
        form = CommitmentForm(request.POST)
        if form.is_valid():
            commitment = form.save(commit=False)
            commitment.investor = investor
            commitment.save()
            messages.success(request, f"Commitment of ₹{commitment.amount_committed} recorded for {investor.name}.")
            return redirect('investors:portal-detail', pk=investor.pk)
    else:
        form = CommitmentForm(initial={'commitment_date': timezone.now().date()})
    
    return render(request, 'investors/add_commitment.html', {
        'investor': investor, 
        'form': form
    })