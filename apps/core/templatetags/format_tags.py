# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
#
# Custom template filter = fungsi buatan sendiri yang bisa dipakai di template dengan
# tanda pipa, mis. {{ trip.laba_bersih|rupiah }}. Harus didaftarkan ke `register` dan
# file-nya ditaruh di folder templatetags/. Di template, panggil {% load format_tags %} dulu.
from django import template
from decimal import Decimal, InvalidOperation
from datetime import date, datetime

register = template.Library()   # wadah pendaftaran filter; namanya wajib 'register'


@register.filter
def rupiah(value):
    """Format angka ke format Rupiah Indonesia: 1400000 -> Rp 1.400.000"""
    try:
        value = Decimal(str(value))   # ubah ke Decimal biar aman untuk uang
        # angka minus ditampilkan dengan tanda minus di depan Rp
        if value < 0:
            return f"-Rp {format_dots(abs(value))}"
        return f"Rp {format_dots(value)}"
    except (ValueError, TypeError, InvalidOperation):
        # kalau bukan angka (mis. None/teks), kembalikan apa adanya supaya tidak error di template
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
        # strftime: ubah objek tanggal jadi teks sesuai pola. %d=tanggal %m=bulan %Y=tahun.
        if isinstance(value, (date, datetime)):
            return value.strftime('%d/%m/%Y')
        return value
    except (AttributeError, ValueError):
        return value


# Fungsi bantu (bukan filter, tidak ada @register). Tugasnya menyisipkan titik tiap 3 digit.
def format_dots(value):
    """Format number with dots as thousand separator (Indonesian style)."""
    # kalau angkanya bulat, buang desimalnya (1400000.0 -> "1400000")
    if value == int(value):
        s = str(int(value))
    else:
        s = f"{value:,.2f}".replace(',', '.')
        return s

    # tempel titik tiap kelipatan 3 digit dari belakang: "1400000" -> "1.400.000"
    result = ''
    for i, digit in enumerate(reversed(s)):
        if i > 0 and i % 3 == 0:
            result = '.' + result
        result = digit + result
    return result
