from django import template
from core.utils.formatting import format_amount

register = template.Library()

@register.filter
def currency(value):
    """
    Usage: {{ value|currency }}
    Output: ₹1,00,000.00
    """
    return format_amount(value, unit=None)

@register.filter
def crore(value):
    """
    Usage: {{ value|crore }}
    Output: ₹1.50 Cr
    """
    return format_amount(value, unit='crore')

@register.filter
def lakh(value):
    """
    Usage: {{ value|lakh }}
    Output: ₹10.50 L
    """
    return format_amount(value, unit='lakh')

@register.filter
def million(value):
    """
    Usage: {{ value|million }}
    Output: $1.50 Mn
    """
    return format_amount(value, unit='million')