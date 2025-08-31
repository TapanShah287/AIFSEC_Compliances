from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import InvesteeCompany
from django.http import JsonResponse

try:
    from .models import Shareholding
except Exception:
    Shareholding = None

@login_required
def investee_company_detail(request, company_id:int):
    company = get_object_or_404(InvesteeCompany, pk=company_id)

    snapshot = []
    total_eq = 0
    if Shareholding is not None:
        eq_qs = Shareholding.objects.filter(investee_company=company, share_type='EQ').select_related('investor')
        total_eq = sum(int(r.number_of_shares or 0) for r in eq_qs)
        if total_eq:
            for r in eq_qs:
                holder = r.investor.name if getattr(r, "investor_id", None) else (getattr(r, "holder_name", None) or "Unspecified Holder")
                pct = (float(r.number_of_shares or 0) * 100.0) / float(total_eq or 1)
                snapshot.append({"holder": holder, "shares": r.number_of_shares, "percent": pct})
            snapshot.sort(key=lambda x: x["percent"], reverse=True)
    context = {"company": company, "shareholding_snapshot": snapshot, "total_eq_shares": total_eq}
    return render(request, "investee_companies/company_detail.html", context)

@login_required
def investee_company_detail_json(request, company_id:int):
    company = get_object_or_404(InvesteeCompany, pk=company_id)
    data = {
        "id": company.pk,
        "name": company.name,
        "sector": getattr(company, "sector", None),
        "incorporation_date": getattr(company, "incorporation_date", None),
        "cin": getattr(company, "cin", None),
    }

    # Minimal shareholding snapshot
    snapshot = []
    total_eq = 0
    if Shareholding is not None:
        qs = Shareholding.objects.filter(investee_company=company, share_type='EQ').select_related('investor')
        total_eq = sum(int(r.number_of_shares or 0) for r in qs) or 1
        for r in qs:
            holder = r.investor.name if getattr(r, "investor_id", None) else (getattr(r, "holder_name", None) or "Unspecified Holder")
            snapshot.append({
                "display_holder": holder,
                "number_of_shares": r.number_of_shares or 0,
                "percent_of_class": (float(r.number_of_shares or 0) * 100.0) / float(total_eq),
            })

    return JsonResponse({
        "company": data,
        "shareholding": snapshot,
        # "financials": [], "valuations": [], "actions": []  # add later if you want
    })


@login_required
def investee_company_shareholding_snapshot_json(request, company_id: int):
    co = get_object_or_404(InvesteeCompany, pk=company_id)
    snapshot, total_eq = [], 0

    if Shareholding is not None:
        # NOTE: if your choices use 'EQUITY' instead of 'EQ', change this filter accordingly.
        qs = Shareholding.objects.filter(investee_company=co, share_type='EQ').select_related('investor')
        total_eq = sum(int(r.number_of_shares or 0) for r in qs) or 1
        for r in qs:
            holder = (
                r.investor.name if getattr(r, "investor_id", None)
                else (getattr(r, "holder_name", None) or "Unspecified Holder")
            )
            pct = (float(r.number_of_shares or 0) * 100.0) / float(total_eq)
            snapshot.append({
                "display_holder": holder,
                "share_type_display": "Equity",
                "number_of_shares": int(r.number_of_shares or 0),
                "percent_of_class": pct,
                "as_of_date": getattr(r, "as_of_date", None),
            })
        snapshot.sort(key=lambda x: x["percent_of_class"], reverse=True)

    return JsonResponse({"results": snapshot, "total_eq": total_eq if total_eq != 1 else 0})