from django import template
from decimal import Decimal

register = template.Library()

@register.simple_tag
def convert_currency(amount, selected_currency):
    if not amount or not selected_currency:
        return amount

    try:
        rate = selected_currency.exchange_rate
        converted = Decimal(amount) * rate
        return f"{selected_currency.symbol}{round(converted, 2)}"
    except:
        return amount