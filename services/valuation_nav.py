# services/valuation_nav.py
from decimal import Decimal
from django.db.models import Sum
from investee_companies.models import Valuation
from transactions.models import PurchaseTransaction, RedemptionTransaction
from core.utils.formatting import format_amount

def positions_for_fund(fund):
    # naive aggregation: buys - sells per company/share_class
    buys = (
        PurchaseTransaction.objects.filter(fund=fund)
        .values("company_id","share_class_id")
        .annotate(qty=Sum("quantity"), cost=Sum("price"))
    )
    sells = (
        RedemptionTransaction.objects.filter(fund=fund)
        .values("company_id","share_class_id")
        .annotate(qty=Sum("quantity"))
    )
    pos = {}
    for b in buys:
        key = (b["company_id"], b["share_class_id"])
        pos[key] = {"qty": Decimal(b["qty"] or 0)}
    for s in sells:
        key = (s["company_id"], s["share_class_id"])
        pos.setdefault(key, {"qty": Decimal(0)})
        pos[key]["qty"] -= Decimal(s["qty"] or 0)
    return pos

def latest_price(company_id, share_class_id):
    v = Valuation.objects.filter(company_id=company_id, share_class_id=share_class_id).order_by("-as_on_date").first()
    return Decimal(v.price_per_share) if v else None

def portfolio_snapshot(fund, display_unit=None):
    pos = positions_for_fund(fund)
    rows = []
    mv_total = Decimal(0)
    for (company_id, share_class_id), data in pos.items():
        qty = Decimal(data["qty"] or 0)
        if qty <= 0: 
            continue
        price = latest_price(company_id, share_class_id) or Decimal(0)
        mv = qty * price
        mv_total += mv
        rows.append({
            "company_id": company_id,
            "share_class_id": share_class_id,
            "quantity": str(qty),
            "last_price": str(price),
            "market_value": str(mv),
            "market_value_display": format_amount(mv, unit=display_unit),
        })
    return {"positions": rows, "total_market_value": str(mv_total), "total_market_value_display": format_amount(mv_total, unit=display_unit)}

def nav_calculation(fund, display_unit=None):
    # Simplified: NAV = MV only (ignores cash/liabilities here). Extend with CashLedger as needed.
    snap = portfolio_snapshot(fund, display_unit=display_unit)
    return {"fund_id": fund.id, "nav_basis": "MV-only (scaffold)", **snap}