from decimal import Decimal
from .models import Currency, ExchangeRate
from django.core.cache import cache

def get_exchange_rate(from_currency_code, date):
    """
    Fetches the exchange rate for a specific date. 
    Falls back to the most recent rate if exact date missing.
    """
    # 1. Check if Base
    try:
        base = Currency.objects.get(is_base=True)
        if from_currency_code == base.code:
            return Decimal('1.0')
    except Currency.DoesNotExist:
        return Decimal('1.0') # Default to 1 if no base set

    # 2. Fetch Rate
    rate_obj = ExchangeRate.objects.filter(
        currency__code=from_currency_code, 
        date__lte=date
    ).order_by('-date').first()

    if rate_obj:
        return rate_obj.rate
    return Decimal('1.0') # Fallback warning: No rate found

def convert_amount(amount, from_code, to_code, date):
    """
    Converts an amount from one currency to another using the DB rates.
    """
    if from_code == to_code:
        return amount
    
    # Convert to Base first (if from_code is not base)
    rate_to_base = get_exchange_rate(from_code, date)
    amount_in_base = amount * rate_to_base
    
    # If target is base, we are done
    base = Currency.objects.filter(is_base=True).first()
    if not base or to_code == base.code:
        return amount_in_base
        
    # If target is NOT base, convert Base -> Target
    # (Rate stored is 1 Foreign = X Base, so 1 Base = 1/X Foreign)
    rate_of_target = get_exchange_rate(to_code, date)
    if rate_of_target == 0: return Decimal('0.0')
    
    return amount_in_base / rate_of_target