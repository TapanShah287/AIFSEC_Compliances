# core/utils/formatting.py
from decimal import Decimal, ROUND_HALF_UP

UNIT_MAP = {
    "crore": Decimal("10000000"),
    "million": Decimal("1000000"),
    "thousand": Decimal("1000"),
    "lakh": Decimal("100000"),
    None: Decimal("1"),
}

def format_amount(amount, unit: str | None = None, currency: str = "₹", places: int = 2):
    if amount is None:
        return "-"
    try:
        amt = Decimal(str(amount))
    except Exception:
        return str(amount)
    factor = UNIT_MAP.get(unit, Decimal("1"))
    val = (amt / factor).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)
    suffix = {
        "crore": " Cr",
        "million": " Mn",
        "thousand": " K",
        "lakh": " Lakh",
        None: "",
    }.get(unit, "")
    return f"{currency}{val:,.{places}f}{suffix}"