from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, OuterRef, Subquery, DateField
from django.db.models.functions import Cast
from .models import InvesteeCompany, ShareValuation, CompanyFinancials, CorporateAction, Shareholding, ValuationReport
from .serializers import CompanySerializer, ShareValuationSerializer, CompanyFinancialsSerializer, CorporateActionSerializer, ShareholdingSerializer
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import ShareholdingForm, ShareValuationForm, ShareholdingPatternForm 
from .views_detail_safe import investee_company_detail
from django.http import HttpResponse
from django.utils.timezone import now
import csv
from collections import defaultdict

try:
    from .models import Shareholding
except Exception:
    Shareholding = None

  
class CompanyViewSet(viewsets.ModelViewSet):
    queryset = InvesteeCompany.objects.all().order_by("name")
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"], url_path="shareholding")
    def shareholding(self, request, pk=None):
        company = self.get_object()
        qs = Shareholding.objects.filter(investee_company=company)
        total = qs.aggregate(total=Sum("number_of_shares"))["total"] or 0
        ser = ShareholdingSerializer(qs, many=True, context={"total_company_shares": total})
        return Response(ser.data)

    @action(detail=True, methods=['get'], url_path='actions')
    def corporate_actions(self, request, pk=None):
        """Returns corporate actions for a specific company."""
        company = self.get_object()
        queryset = CorporateAction.objects.filter(investee_company=company).order_by('-action_date')
        serializer = CorporateActionSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def financials(self, request, pk=None):
        """Returns financial data for a specific company."""
        company = self.get_object()
        queryset = CompanyFinancials.objects.filter(investee_company=company).order_by('-period_date')
        serializer = CompanyFinancialsSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def valuations(self, request, pk=None):
        """Returns all share valuations for a specific company."""
        company = self.get_object()
        reports = ValuationReport.objects.filter(investee_company=company)
        queryset = ShareValuation.objects.filter(valuation_report__in=reports).order_by('-valuation_report__valuation_date')
        serializer = ShareValuationSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="market-valuation")
    def market_valuation(self, request, pk=None):
        company = self.get_object()

        # total shares by share_type from Shareholding
        shares = (Shareholding.objects
                  .filter(investee_company=company)
                  .values("share_type")
                  .annotate(total_shares=Sum("number_of_shares")))

        # latest valuation per share_type via ShareValuation -> valuation_report.date
        latest_val_date = (ShareValuation.objects
            .filter(share_capital__investee_company=company,
                    share_capital__share_type=OuterRef("share_type"))
            .order_by("-valuation_report__valuation_date")
            .values("valuation_report__valuation_date")[:1])

        latest_val_psv = (ShareValuation.objects
            .filter(share_capital__investee_company=company,
                    share_capital__share_type=OuterRef("share_type"))
            .order_by("-valuation_report__valuation_date")
            .values("per_share_value")[:1])

        choices_map = dict(Shareholding._meta.get_field("share_type").choices or [])

        annotated = shares.annotate(
            latest_date=Cast(Subquery(latest_val_date, output_field=DateField()), output_field=DateField()),
            psv=Subquery(latest_val_psv),
        )

        rows, total_mcap = [], 0
        for r in annotated:
            cls = r["share_type"]
            n = int(r["total_shares"] or 0)
            psv = float(r["psv"] or 0)
            mcap = n * psv
            total_mcap += mcap
            rows.append({
                "share_type": cls,
                "share_type_display": choices_map.get(cls, cls),
                "shares": n,
                "per_share_value": psv,
                "valuation_date": (r["latest_date"].isoformat() if r["latest_date"] else None),
                "market_value": mcap,
            })

        # as_of = max date in rows (if any)
        as_of = None
        for r in rows:
            if r["valuation_date"]:
                as_of = max(as_of or r["valuation_date"], r["valuation_date"])

        return Response({
            "company": company.pk,
            "as_of": as_of,
            "classes": rows,
            "total_market_cap": total_mcap,
        })

@login_required
def redirect_company_detail(request, pk):
    return redirect('investee_companies:investee_company_detail', company_id=pk)
    
@login_required
def add_shareholding(request, company_id: int):
    company = get_object_or_404(InvesteeCompany, pk=company_id)

    if request.method == "POST":
        form = ShareholdingPatternForm(request.POST)
        if form.is_valid():
            sh = form.save(commit=False)
            sh.investee_company = company     # force the FK
            sh.save()
            # After save, return to the portal detail so you can see the table update
            return redirect("portal-company-detail", pk=company.pk)
    else:
        form = ShareholdingPatternForm(initial={"investee_company": company})

    return render(request, "investee_companies/add_shareholding.html", {
        "company": company,
        "form": form,
        "pattern_mode": True,   # use in the template to hide ledger fields if it was generic
    })

@login_required
def add_share_valuation(request, company_id: int):
    company = get_object_or_404(InvesteeCompany, pk=company_id)

    if request.method == "POST":
        form = ShareValuationForm(request.POST, company=company)
        if form.is_valid():
            form.save()
            return redirect("portal-company-detail", pk=company.pk)
    else:
        form = ShareValuationForm(company=company)

    return render(
        request,
        "investee_companies/add_share_valuation.html",
        {"company": company, "form": form},
    )
    
@login_required
def company_cap_table(request, company_id):
    import csv
    from django.http import HttpResponse
    company = get_object_or_404(InvesteeCompany, pk=company_id)
    # Fetch all shareholdings for this company
    rows = list(Shareholding.objects.filter(investee_company=company).select_related('investor'))
    # Compute totals by share_type
    from collections import defaultdict
    totals_by_type = defaultdict(int)
    for r in rows:
        totals_by_type[r.share_type] += int(r.number_of_shares or 0)

    # Build grouped data
    grouped = defaultdict(list)
    for r in rows:
        total_for_type = totals_by_type.get(r.share_type, 0) or 1
        pct = (float(r.number_of_shares or 0) * 100.0) / float(total_for_type)
        grouped[r.share_type].append({
            'holder': r.investor.name if r.investor_id else (r.holder_name or 'Unspecified Holder'),
            'number_of_shares': r.number_of_shares,
            'face_value': r.face_value,
            'total_face_value': (r.face_value or 0) * (r.number_of_shares or 0),
            'percent_of_class': pct,
            'percent_of_total': (float(r.number_of_shares or 0) * 100.0 / float(sum(totals_by_type.values()) or 1)),
        })

    # Compute grand totals
    grand_total_shares = sum(totals_by_type.values()) or 0

    # Provide human labels
    type_labels = {'EQ': 'Equity', 'PREF': 'Preference'}
    # CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="cap_table_{company.id}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Class','Shareholder','Shares','% of Class','% of Total','Face Value','Total Face'])
        for s_type, rows_g in grouped.items():
            for row in rows_g:
                writer.writerow([s_type, row['holder'], row['number_of_shares'], f"{row['percent_of_class']:.2f}%", f"{row['percent_of_total']:.2f}%", row['face_value'], row['total_face_value']])
        return response

    context = {
        'company': company,
        'grouped': grouped,
        'type_labels': type_labels,
        'totals_by_type': totals_by_type,
        'grand_total_shares': grand_total_shares,
    }
    return render(request, 'investee_companies/cap_table.html', context)

@login_required
def investee_company_detail(request, company_id: int):
    """
    Safe detail view: NO ShareCapital dependency.
    Renders server HTML template `investee_companies/company_detail.html`
    with a minimal snapshot context.
    """
    company = get_object_or_404(InvesteeCompany, pk=company_id)

    snapshot = []
    total_eq = 0
    if Shareholding is not None:
        # Adjust 'EQ' if your choice value differs (e.g., 'EQUITY')
        qs = (Shareholding.objects
              .filter(investee_company=company, share_type='EQ')
              .select_related('investor'))
        total_eq = sum(int(r.number_of_shares or 0) for r in qs)
        if total_eq:
            for r in qs:
                holder = (
                    (r.investor.name if getattr(r, "investor_id", None) else None)
                    or getattr(r, "holder_name", None)
                    or "Unspecified Holder"
                )
                pct = (float(r.number_of_shares or 0) * 100.0) / float(total_eq or 1)
                snapshot.append({"holder": holder, "shares": r.number_of_shares, "percent": pct})
            snapshot.sort(key=lambda x: x["percent"], reverse=True)

    ctx = {
        "company": company,
        "shareholding_snapshot": snapshot,
        "total_eq_shares": total_eq,
    }
    return render(request, "investee_companies/company_detail.html", ctx)
        

@login_required
def company_shareholding_pattern(request, company_id):
    company = get_object_or_404(InvesteeCompany, pk=company_id)
    rows = list(
        Shareholding.objects
        .filter(investee_company=company)
        .select_related('investor')
    )

    # Totals by class and grand total
    totals_by_type = defaultdict(int)
    for r in rows:
        totals_by_type[r.share_type] += int(r.number_of_shares or 0)
    grand_total = sum(totals_by_type.values()) or 0

    # Group for template/CSV
    grouped = defaultdict(list)
    for r in rows:
        holder = r.investor.name if r.investor_id else (r.holder_name or 'Unspecified Holder')
        cls_total = totals_by_type.get(r.share_type, 0) or 1
        shares = int(r.number_of_shares or 0)
        face = (r.face_value or 0)
        grouped[r.share_type].append({
            'holder': holder,
            'shares': shares,
            'pct_class': (float(shares) * 100.0 / float(cls_total)),
            'pct_total': (float(shares) * 100.0 / float(grand_total)) if grand_total else 0.0,
            'face_value': face,
            'total_face_value': float(face) * float(shares),
        })

    type_labels = {'EQ': 'Equity', 'PREF': 'Preference'}

    # CSV export (use the SAME keys you created above)
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="shareholding_pattern_{company.id}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Class','Shareholder','Shares','% of Class','% of Total','Face Value','Total Face'])
        for s_type, rows_g in grouped.items():
            for row in rows_g:
                writer.writerow([
                    s_type,
                    row['holder'],
                    row['shares'],
                    f"{row['pct_class']:.2f}%",
                    f"{row['pct_total']:.2f}%",
                    row['face_value'],
                    f"{row['total_face_value']:.2f}",
                ])
        return response

    context = {
        'company': company,
        'grouped': grouped,
        'totals_by_type': totals_by_type,
        'grand_total': grand_total,
        'type_labels': type_labels,
    }
    return render(request, 'investee_companies/shareholding_pattern.html', context)
