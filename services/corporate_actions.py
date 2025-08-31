# services/corporate_actions.py
from django.db import transaction
from decimal import Decimal

# This is a placeholder scaffold. Plug in your actual ShareCapital/Position models.
def parse_ratio(ratio: str) -> Decimal:
    # supports formats like "2:1" or "1:2"
    a, b = ratio.split(":")
    return Decimal(a) / Decimal(b)

@transaction.atomic
def create_corporate_action(company, payload: dict):
    """Create/apply a corporate action for a company and adjust cap table + positions.
    payload = {event_type, ex_date, ratio, notes}
    """
    event_type = payload.get("event_type")
    ratio = payload.get("ratio")
    ratio_factor = parse_ratio(ratio) if ratio else Decimal(1)

    # TODO: persist CorporateAction model if present
    # TODO: adjust ShareCapital by ratio
    # TODO: adjust all fund positions for this company's share classes by ratio
    # Use select_for_update on rows you modify and store an idempotency key derived from (company, event_type, ex_date).
    return {"company": company.id, "event_type": event_type, "ratio": ratio, "status": "APPLIED (scaffold)"}  # placeholder