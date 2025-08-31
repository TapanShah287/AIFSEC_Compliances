# funds/services/portfolio.py
from collections import defaultdict
from django.db.models import Sum, Max
from django.utils import timezone

# Best-effort field accessors (so we don't need to change your models)

def _get_qty(obj):
    for f in ("units", "quantity", "number_of_shares", "shares", "no_of_units"):
        if hasattr(obj, f):
            return getattr(obj, f) or 0
    # Fallback: try amount/price
    if hasattr(obj, "amount") and hasattr(obj, "price_per_unit"):
        try:
            return (obj.amount or 0) / (obj.price_per_unit or 1)
        except Exception:
            return 0
    return 0


def _get_amount(obj):
    for f in ("amount", "gross_amount", "net_amount", "total_amount"):
        if hasattr(obj, f):
            return getattr(obj, f) or 0
    # Fallback from qty * price
    if hasattr(obj, "price_per_unit"):
        return (_get_qty(obj) or 0) * (getattr(obj, "price_per_unit") or 0)
    return 0


def compute_fund_positions(Fund, PurchaseTransaction, RedemptionTransaction, ValuationReport):
    """
    Returns a dict keyed by (fund_id, investee_company_id) with:
      qty_held, invested_cost, current_value, unrealised_gain, unrealised_gain_pct,
      last_valuation_date, fair_value_per_share (if available)
    """
    # Aggregate purchases
    purchases = PurchaseTransaction.objects.values(
        "fund_id", "investee_company_id"
    ).annotate(
        qty=Sum("quantity", default=0) if hasattr(PurchaseTransaction, "quantity") else Sum("id")*0,
        amount=Sum("amount", default=0),
    )

    # Gracefully recompute qty if quantity field isn't present
    p_map = defaultdict(lambda: {"qty": 0.0, "amount": 0.0})
    for p in PurchaseTransaction.objects.all():
        key = (getattr(p, "fund_id"), getattr(p, "investee_company_id"))
        p_map[key]["qty"] += float(_get_qty(p))
        p_map[key]["amount"] += float(_get_amount(p))

    # Aggregate redemptions
    r_map = defaultdict(lambda: {"qty": 0.0, "amount": 0.0})
    for r in RedemptionTransaction.objects.all():
        key = (getattr(r, "fund_id"), getattr(r, "investee_company_id"))
        r_map[key]["qty"] += float(_get_qty(r))
        r_map[key]["amount"] += float(_get_amount(r))

    # Latest valuation per investee company
    latest_vals = {}
    if ValuationReport is not None:
        # We assume ValuationReport has fields: investee_company, report_date, fair_value_per_share
        qs = (ValuationReport.objects
              .values("investee_company_id")
              .annotate(last_date=Max("report_date")))
        last_dates = {row["investee_company_id"]: row["last_date"] for row in qs}
        for ic_id, dt in last_dates.items():
            vr = (ValuationReport.objects
                  .filter(investee_company_id=ic_id, report_date=dt)
                  .first())
            if vr and hasattr(vr, "fair_value_per_share"):
                latest_vals[ic_id] = {
                    "fvps": float(vr.fair_value_per_share or 0),
                    "date": vr.report_date,
                }

    # Build positions
    positions = {}
    keys = set(p_map.keys()) | set(r_map.keys())
    for key in keys:
        p = p_map.get(key, {"qty": 0.0, "amount": 0.0})
        r = r_map.get(key, {"qty": 0.0, "amount": 0.0})
        qty_held = p["qty"] - r["qty"]
        invested_cost = p["amount"]  # simple: total purchases; you can subtract avg cost of redeemed if needed
        ic_id = key[1]
        fvps = latest_vals.get(ic_id, {}).get("fvps", 0.0)
        current_value = qty_held * fvps
        unrealised_gain = current_value - invested_cost
        unrealised_gain_pct = (unrealised_gain / invested_cost * 100.0) if invested_cost else 0.0
        positions[key] = {
            "qty_held": round(qty_held, 4),
            "invested_cost": round(invested_cost, 2),
            "current_value": round(current_value, 2),
            "unrealised_gain": round(unrealised_gain, 2),
            "unrealised_gain_pct": round(unrealised_gain_pct, 2),
            "fair_value_per_share": fvps,
            "last_valuation_date": latest_vals.get(ic_id, {}).get("date"),
        }
    return positions