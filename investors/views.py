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
from django.db.models import Q, Value
from django.db.models.functions import Coalesce

# Local Imports
from .models import Investor, InvestorDocument
from .forms import InvestorForm, InvestorDocumentForm, BankDetailForm
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
    queryset = Investor.objects.annotate(
        annotated_commitment=Coalesce(Sum('commitments__amount_committed'), Value(0)),
        annotated_contribution=Coalesce(Sum('receipts__amount_received'), Value(0)) 
    ).order_by('name')
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
    active_id = request.session.get('active_entity_id')
    query = request.GET.get('q', '')
    investors_queryset = Investor.objects.all().order_by('name')
    base_investors = Investor.objects.filter(
        manager_entities__id=active_id
    ).distinct()

    if query:
        investors = investors.filter(
            Q(name__icontains=query) | 
            Q(pan__icontains=query) | 
            Q(email__icontains=query)
        )

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

# 1. Total Commitments (Aggregate across all investors)
    total_committed_aggregate = InvestorCommitment.objects.filter(
        fund__manager_entity_id=active_id
    ).aggregate(total=Sum('amount_committed'))['total'] or 0

    # 2. Total Contributed (Aggregate across all receipts)
    total_contributed_aggregate = DrawdownReceipt.objects.filter(
        fund__manager_entity_id=active_id
    ).aggregate(total=Sum('amount_received'))['total'] or 0

    # 3. Pending KYC Count
    pending_kyc_count = base_investors.filter(kyc_status='PENDING').count()

# --- INDIVIDUAL ROW LOGIC ---

    investors_data = []

    for investor in base_investors.order_by('name'):
        # Commitment for this specific investor
        committed = InvestorCommitment.objects.filter(
            investor=investor, 
            fund__manager_entity_id=active_id
        ).aggregate(total=Sum('amount_committed'))['total'] or 0
        
        # Contribution for this specific investor
        contributed = DrawdownReceipt.objects.filter(
            investor=investor, 
            fund__manager_entity_id=active_id
        ).aggregate(total=Sum('amount_received'))['total'] or 0
        
        # Calculate Funded Percentage for the progress bar
        funded_pct = (contributed / committed * 100) if committed > 0 else 0

        investors_data.append({
            'investor': investor, # Accessible in template as item.investor.name
            'total_committed': committed / scale,
            'uncalled_capital': (committed - contributed) / scale,
            'funded_pct': round(funded_pct, 2),
            'kyc_status': investor.kyc_status,
        })

    return render(request, 'investors/investor_list.html', {
        'investors': investors_data,
        'total_committed_aggregate': total_committed_aggregate / scale,
        'total_contributed_aggregate': total_contributed_aggregate / scale,
        'pending_kyc_count': pending_kyc_count,
        'suffix': suffix,
        'denom': denom,
    })

@login_required
def portal_investor_detail(request, pk):
    """
    Detailed dashboard for a single investor.
    Shows cross-fund commitments, uncalled capital, and document vault.
    """
    investor = get_object_or_404(Investor, pk=pk)
    is_compliance_user = request.user.groups.filter(name='Compliance').exists()
    
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
        'is_compliance_user': is_compliance_user,
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
    active_entity_id = request.session.get('active_entity_id')

    if request.method == "POST":
        form = InvestorForm(request.POST)
        if form.is_valid():
            investor = form.save()
            if active_entity_id:
                investor.manager_entities.add(active_entity_id)

            messages.success(request, f"Investor '{investor.name}' registered. Please upload KYC documents.")
            return redirect('investors:portal-detail', pk=investor.pk)
    else:
        form = InvestorForm(active_manager=active_entity_id)
    
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

# ==========================================
# 3. Document Management Views (HTML Templates)
# ==========================================

@login_required
def investor_upload_doc(request, pk):
    """
    Handles uploading KYC documents for a specific investor.
    """
    investor = get_object_or_404(Investor, pk=pk)
    
    if request.method == 'POST':
        form = InvestorDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.investor = investor
            
            # Auto-verification logic: 
            # If the uploader is a Compliance Officer, auto-verify. 
            # For now, we leave it as Pending.
            doc.is_verified = False 
            
            doc.save()
            messages.success(request, f"{doc.get_doc_type_display()} uploaded successfully.")
            return redirect('investors:portal-detail', pk=investor.pk)
    else:
        form = InvestorDocumentForm()

    return render(request, 'investors/document_form.html', {
        'form': form,
        'investor': investor
    })

# ==========================================
# 4. Authoriser Views (HTML Templates)
# ==========================================

@login_required
def verify_document(request, doc_pk):
    """
    Toggles the verification status of a specific document.
    Only accessible to users with 'Compliance' or 'Admin' roles.
    """
    doc = get_object_or_404(InvestorDocument, pk=doc_pk)
    
    # Logic to ensure only Compliance Officers can verify
    if not request.user.groups.filter(name='Compliance').exists():
        messages.error(request, "Unauthorized: Only Compliance can verify documents.")
        return redirect('investors:portal-detail', pk=doc.investor.pk)

    doc.is_verified = True
    doc.verified_at = timezone.now()
    doc.verified_by = request.user
    doc.save()
    
    # Check if all mandatory docs are now verified
    check_and_update_kyc_status(doc.investor)
    
    messages.success(request, f"{doc.get_doc_type_display()} has been verified.")
    return redirect('investors:portal-detail', pk=doc.investor.pk)

def check_and_update_kyc_status(investor):
    """
    Business logic: If mandatory docs exist and are verified, 
    mark investor as VERIFIED.
    """
    mandatory_types = ['PAN', 'BANK_PROOF']
    NON_INDIVIDUAL_TYPES = ['COMPANY', 'LLP', 'TRUST', 'FPI']
    if investor.investor_type in NON_INDIVIDUAL_TYPES:
        mandatory_types.append('FATCA_CRS')
        mandatory_types.append('ACCREDITATION_CERT')

        
    verified_types = investor.documents.filter(is_verified=True).values_list('doc_type', flat=True)
    
    if all(mtype in verified_types for mtype in mandatory_types):
        investor.kyc_status = 'VERIFIED'
        investor.save()

# investors/views.py

@login_required
def portal_investor_edit(request, pk):
    """
    Handles editing an existing investor profile.
    """
    investor = get_object_or_404(Investor, pk=pk)
    
    if request.method == 'POST':
        form = InvestorForm(request.POST, instance=investor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Profile for {investor.name} updated successfully.")
            return redirect('investors:portal-detail', pk=investor.pk)
    else:
        form = InvestorForm(instance=investor)
    
    return render(request, 'investors/investor_form.html', {
        'form': form, 
        'title': 'Edit Investor Profile',
        'button_text': 'Update Profile'
    })

@login_required
def investor_add_bank(request, pk):
    """
    Adds a bank account to a specific investor.
    """
    investor = get_object_or_404(Investor, pk=pk)
    
    if request.method == 'POST':
        form = BankDetailForm(request.POST, request.FILES)
        if form.is_valid():
            bank_detail = form.save(commit=False)
            bank_detail.investor = investor
            
            # Logic: If this is the first account, make it primary automatically
            if not investor.bank_details.exists():
                bank_detail.is_primary = True
                
            bank_detail.save()
            messages.success(request, f"Bank account {bank_detail.account_number} added successfully.")
            return redirect('investors:portal-detail', pk=investor.pk)
    else:
        # Pre-fill account holder name with investor name for convenience
        form = BankDetailForm(initial={'account_holder_name': investor.name})
    
    return render(request, 'investors/bank_form.html', {
        'form': form,
        'investor': investor
    })