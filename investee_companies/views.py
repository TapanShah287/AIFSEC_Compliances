from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q, ExpressionWrapper, DecimalField
from django.db import transaction
from decimal import Decimal
import json

# DRF Imports
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

# Local Imports
from .models import (
    InvesteeCompany, Shareholding, ValuationReport, 
    ShareValuation, ShareCapital, CorporateAction, CompanyFinancials
)
from .forms import (
    InvesteeCompanyForm, ShareholdingForm, 
    ValuationReportForm, ShareValuationFormSet, ShareCapitalFormSet
)
from .serializers import (
    CompanySerializer, ShareValuationSerializer, 
    CompanyFinancialsSerializer, CorporateActionSerializer,
    ShareholdingSerializer
)

# Cross-App Imports (For Cost Basis Calculation)
# We use string references in models, but here we need the actual model for querying
from transactions.models import PurchaseTransaction

# =========================================================
#  1. API VIEWSETS (Backend Data for api/urls.py)
# =========================================================

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = InvesteeCompany.objects.all().order_by('name')
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def cap_table(self, request, pk=None):
        company = self.get_object()
        holdings = Shareholding.objects.filter(investee_company=company)
        serializer = ShareholdingSerializer(holdings, many=True)
        return Response(serializer.data)

class ShareValuationViewSet(viewsets.ModelViewSet):
    queryset = ShareValuation.objects.all().select_related('valuation_report', 'share_capital')
    serializer_class = ShareValuationSerializer
    permission_classes = [IsAuthenticated]

class CompanyFinancialsViewSet(viewsets.ModelViewSet):
    queryset = CompanyFinancials.objects.all()
    serializer_class = CompanyFinancialsSerializer
    permission_classes = [IsAuthenticated]

class CorporateActionViewSet(viewsets.ModelViewSet):
    queryset = CorporateAction.objects.all()
    serializer_class = CorporateActionSerializer
    permission_classes = [IsAuthenticated]


# =========================================================
#  2. HTML PORTAL VIEWS (Frontend Pages)
# =========================================================

@login_required
def company_list_view(request):
    """Lists all investee companies with optional search filtering."""
    query = request.GET.get('q')
    companies = InvesteeCompany.objects.all().order_by('name')
    if query:
        companies = companies.filter(Q(name__icontains=query) | Q(cin__icontains=query))
    return render(request, 'investee_companies/companies.html', {'companies': companies})

@login_required
def company_add_view(request):
    """
    Onboard a new company AND define its Opening Capital Structure.
    """
    if request.method == 'POST':
        form = InvesteeCompanyForm(request.POST)
        # Prefix 'capital' must match the template ID logic
        capital_formset = ShareCapitalFormSet(request.POST, prefix='capital')
        
        if form.is_valid() and capital_formset.is_valid():
            with transaction.atomic():
                company = form.save()
                
                instances = capital_formset.save(commit=False)
                for instance in instances:
                    instance.investee_company = company
                    instance.save()
                
            messages.success(request, f"Company '{company.name}' and capital structure onboarded successfully.")
            return redirect('investee_companies:portal-list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = InvesteeCompanyForm()
        # Initial empty formset
        capital_formset = ShareCapitalFormSet(prefix='capital', queryset=ShareCapital.objects.none())
    
    return render(request, 'investee_companies/add_investee_company.html', {
        'form': form, 
        'capital_formset': capital_formset
    })

@login_required
def company_detail_view(request, pk):
    """
    Dashboard showing official capital structure totals.
    Units are pulled from ShareCapital.issued_shares (The pool).
    """
    company = get_object_or_404(InvesteeCompany, pk=pk)
    
    structure = []
    for sc in company.share_classes.all():
        # Using issued_shares as the source of truth for "Total Units"
        units = sc.issued_shares or 0
        structure.append({
            'instrument': sc.get_share_type_display(),
            'class_name': sc.class_name,
            'face_value': sc.face_value,
            'total_units': units,
            'total_capital': Decimal(units) * sc.face_value
        })

    fund_holdings = Shareholding.objects.filter(
        investee_company=company,
        investor__isnull=False
    ).values(
        'investor__name', 'share_capital__class_name', 'share_capital__share_type'
    ).annotate(
        units=Sum('number_of_shares')
    ).order_by('investor__name')

    valuation_history = ShareValuation.objects.filter(
        share_capital__investee_company=company
    ).select_related('valuation_report', 'share_capital').order_by('valuation_report__valuation_date')
    
    chart_data = {
        'labels': [v.valuation_report.valuation_date.strftime('%Y-%m-%d') for v in valuation_history],
        'values': [float(v.per_share_value) for v in valuation_history]
    }

    return render(request, 'investee_companies/company_detail.html', {
        'company': company,
        'structure': structure,
        'fund_holdings': fund_holdings,
        'chart_data_json': json.dumps(chart_data),
        'corporate_actions': company.corporate_actions.all().order_by('-action_date'),
        'financials': company.financials.all().order_by('-financial_year')
    })

@login_required
def manage_capital_structure(request, pk):
    """
    View to Edit/Add Share Classes (Capital Structure) for an existing company.
    """
    company = get_object_or_404(InvesteeCompany, pk=pk)
    
    if request.method == 'POST':
        formset = ShareCapitalFormSet(
            request.POST, 
            queryset=ShareCapital.objects.filter(investee_company=company),
            prefix='capital'
        )
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.investee_company = company
                instance.save()
            
            # Handle Deletions
            for obj in formset.deleted_objects:
                obj.delete()
                
            messages.success(request, "Capital structure updated successfully.")
            return redirect('investee_companies:portal-detail', pk=company.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        formset = ShareCapitalFormSet(
            queryset=ShareCapital.objects.filter(investee_company=company),
            prefix='capital'
        )

    return render(request, 'investee_companies/manage_capital_structure.html', {
        'company': company,
        'formset': formset
    })

@login_required
def cap_table_view(request, pk):
    """
    Detailed Cap Table with Residual Calculation for "Other Shareholders".
    Total per class remains constant = ShareCapital.issued_shares.
    """
    company = get_object_or_404(InvesteeCompany, pk=pk)
    share_classes = company.share_classes.all()
    
    # Calculate global totals for percentage calculations
    grand_total_pool = share_classes.aggregate(t=Sum('issued_shares'))['t'] or Decimal('0')
    
    grouped = {}
    for sc in share_classes:
        # 1. Get all specific shareholders for this class
        holdings = Shareholding.objects.filter(share_capital=sc).select_related('investor')
        
        pool_total = sc.issued_shares
        known_units = holdings.aggregate(t=Sum('number_of_shares'))['t'] or Decimal('0')
        residual_units = pool_total - known_units
        
        rows = []
        # Add specific holders
        for h in holdings:
            rows.append({
                'holder': h.display_holder,
                'number_of_shares': h.number_of_shares,
                'total_face_value': h.number_of_shares * sc.face_value,
                'percent_of_class': (h.number_of_shares / pool_total * 100) if pool_total > 0 else 0,
                'percent_of_total': (h.number_of_shares / grand_total_pool * 100) if grand_total_pool > 0 else 0
            })
            
        # 2. Add "Other Shareholders" if there's a residual balance
        if residual_units > 0:
            rows.append({
                'holder': "Other Shareholders (Unclassified)",
                'is_residual': True,
                'number_of_shares': residual_units,
                'total_face_value': residual_units * sc.face_value,
                'percent_of_class': (residual_units / pool_total * 100) if pool_total > 0 else 0,
                'percent_of_total': (residual_units / grand_total_pool * 100) if grand_total_pool > 0 else 0
            })
            
        grouped[sc.id] = {
            'label': f"{sc.class_name} ({sc.get_share_type_display()})",
            'rows': rows,
            'total_units': pool_total,
            'total_face_value': pool_total * sc.face_value
        }

    return render(request, 'investee_companies/cap_table.html', {
        'company': company,
        'grouped': grouped,
        'grand_total_pool': grand_total_pool
    })

@login_required
def add_shareholding(request, pk):
    """View to add a shareholding entry (manual or investor-linked)."""
    company = get_object_or_404(InvesteeCompany, pk=pk)
    if request.method == 'POST':
        form = ShareholdingForm(request.POST, company=company)
        if form.is_valid():
            holding = form.save(commit=False)
            holding.investee_company = company
            holding.save()
            messages.success(request, "Holding record successfully added.")
            return redirect('investee_companies:cap-table', pk=company.pk)
    else:
        form = ShareholdingForm(company=company)
    return render(request, 'investee_companies/add_shareholding.html', {'form': form, 'company': company})

@login_required
def add_valuation_report(request, pk):
    """
    Handles adding a Valuation Report and the associated per-share values.
    """
    company = get_object_or_404(InvesteeCompany, pk=pk)
    share_classes = ShareCapital.objects.filter(investee_company=company)
    
    if request.method == 'POST':
        form = ValuationReportForm(request.POST, request.FILES)
        formset = ShareValuationFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            report = form.save(commit=False)
            report.investee_company = company
            report.save()
            
            instances = formset.save(commit=False)
            for instance in instances:
                instance.valuation_report = report
                instance.save()
            
            messages.success(request, "Valuation report recorded.")
            return redirect('investee_companies:portal-detail', pk=company.pk)
    else:
        form = ValuationReportForm()
        initial = [{'share_capital': sc.id} for sc in share_classes]
        formset = ShareValuationFormSet(initial=initial, queryset=ShareValuation.objects.none())
        
        # Attach labels to sub-forms for template rendering
        for sub_form, sc in zip(formset.forms, share_classes):
            sub_form.initial_share_class_name = sc.class_name

    return render(request, 'investee_companies/add_valuation_report.html', {
        'form': form, 'formset': formset, 'company': company
    })

@login_required
def execute_corporate_action(request, pk):
    """
    Executes Corporate Actions on the pool and holdings.
    """
    company = get_object_or_404(InvesteeCompany, pk=pk)
    if request.method == "POST":
        target_class_id = request.POST.get('target_class')
        action_type = request.POST.get('action_type')
        ratio_from = int(request.POST.get('ratio_from', 1))
        ratio_to = int(request.POST.get('ratio_to', 1))
        
        target_class = get_object_or_404(ShareCapital, id=target_class_id)
        multiplier = Decimal(ratio_to) / Decimal(ratio_from)

        with transaction.atomic():
            # 1. Update Master Pool
            target_class.issued_shares = F('issued_shares') * multiplier
            
            # 2. Update Face Value if Split
            if action_type == 'SPLIT':
                target_class.face_value = F('face_value') / multiplier
            
            target_class.save()

            # 3. Update specific shareholder ledgers
            Shareholding.objects.filter(share_capital=target_class).update(
                number_of_shares = F('number_of_shares') * multiplier
            )

            # 4. Log Action
            CorporateAction.objects.create(
                investee_company=company,
                target_class=target_class,
                action_type=action_type,
                action_date=request.POST.get('action_date'),
                ratio_from=ratio_from,
                ratio_to=ratio_to,
                is_executed=True
            )

        messages.success(request, f"Corporate action {action_type} executed. Pool and individual holdings updated.")
        return redirect('investee_companies:portal-detail', pk=company.pk)
    return render(request, 'investee_companies/add_corporate_action.html', {'company': company, 'share_classes': company.share_classes.all()})