# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django import template
from decimal import Decimal, InvalidOperation
from datetime import date, datetime

register = template.Library()

@register.filter
def rupiah(value):
    """Format angka ke format Rupiah Indonesia: 1400000 → Rp 1.400.000"""
    try:
        value = Decimal(str(value))
        # Handle negative numbers
        if value < 0:
            return f"-Rp {format_dots(abs(value))}"
        return f"Rp {format_dots(value)}"
    except (ValueError, TypeError, InvalidOperation):
        return value
@register.filter
def ribuan(value):
    """Format angka dengan titik sebagai pemisah ribuan (tanpa Rp)"""
    try:
        value = Decimal(str(value))
        if value < 0:
            return f"-{format_dots(abs(value))}"
        return format_dots(value)
    except (ValueError, TypeError, InvalidOperation):
        return value

@register.filter
def tgl_indo(value):
    """Format tanggal ke DD/MM/YYYY (format Indonesia)."""
    if value is None:
        return '-'
    try:
        if isinstance(value, (date, datetime)):
            return value.strftime('%d/%m/%Y')
        return value
    except (AttributeError, ValueError):
        return value

def format_dots(value):
    """Format number with dots as thousand separator (Indonesian style)."""
    # Convert to integer string (remove decimals if .0)
    if value == int(value):
        s = str(int(value))
    else:
        s = f"{value:,.2f}".replace(',', '.')
        return s

    # Add dots as thousand separators
    result = ''
    for i, digit in enumerate(reversed(s)):
        if i > 0 and i % 3 == 0:
            result = '.' + result
        result = digit + result
    return result
