from decimal import Decimal, ROUND_HALF_UP

UNIT_MAP = {
    "crore": Decimal("10000000"),
    "cr": Decimal("10000000"),
    "million": Decimal("1000000"),
    "mn": Decimal("1000000"),
    "lakh": Decimal("100000"),
    "lk": Decimal("100000"),
    "thousand": Decimal("1000"),
    "k": Decimal("1000"),
    None: Decimal("1"),
}

def format_amount(amount, unit: str | None = None, currency: str = "₹", places: int = 2) -> str:
    """
    Formats a decimal amount into a human-readable string with units.
    Usage: format_amount(15000000, 'crore') -> '₹1.50 Cr'
    """
    if amount is None or amount == "":
        return "-"
    
    try:
        if isinstance(amount, str):
            # Remove commas if passed as string "1,00,000"
            amount = amount.replace(",", "")
        amt = Decimal(str(amount))
    except (ValueError, TypeError):
        return str(amount)

    # Normalize unit key (case-insensitive)
    unit_key = unit.lower() if unit else None
    factor = UNIT_MAP.get(unit_key, Decimal("1"))

    val = (amt / factor).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)
    
    # Standard suffixes
    suffix_map = {
        "crore": " Cr", "cr": " Cr",
        "million": " Mn", "mn": " Mn",
        "lakh": " L", "lk": " L",
        "thousand": " K", "k": " K",
    }
    suffix = suffix_map.get(unit_key, "")
    
    # Indian formatting style for commas (optional, standard comma separation)
    formatted_val = f"{val:,.{places}f}"
    
    return f"{currency}{formatted_val}{suffix}"