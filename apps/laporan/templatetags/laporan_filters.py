# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
# Filter template khusus laporan. Dipakai di template: {{ bulan|nama_bulan }}.
from django import template

register = template.Library()

# index 0 sengaja kosong supaya NAMA_BULAN[1] = 'Januari' (nomor bulan pas dengan indeks).
NAMA_BULAN = [
    '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]

@register.filter
def nama_bulan(value):
    """Ubah nomor bulan (1-12) jadi nama bulan Indonesia."""
    try:
        idx = int(value)
        if 1 <= idx <= 12:
            return NAMA_BULAN[idx]
    except (ValueError, TypeError):
        pass
    return value
