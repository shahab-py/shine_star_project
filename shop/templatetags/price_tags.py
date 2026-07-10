from django import template

register = template.Library()

@register.filter(name='format_price')
def format_price(value):
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value
