# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django import template

register = template.Library()

NAMA_BULAN = [
    '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]

@register.filter
def nama_bulan(value):
    """Convert month number (1-12) to Indonesian month name."""
    try:
        idx = int(value)
        if 1 <= idx <= 12:
            return NAMA_BULAN[idx]
    except (ValueError, TypeError):
        pass
    return value
