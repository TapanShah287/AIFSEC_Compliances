from django import template
register = template.Library()

@register.filter
def get_item(d, k):
    try:
        return d.get(k) if hasattr(d, 'get') else d[k]
    except Exception:
        return None
