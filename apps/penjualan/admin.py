# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.contrib import admin

# Register your models here.

from .models import Penjualan, BagiHasil

@admin.register(Penjualan)
class PenjualanAdmin(admin.ModelAdmin):
    list_display = ['hasil_tangkap', 'pembeli', 'berat_terjual', 'harga_per_kg', 'tgl_jual']
    list_filter = ['tgl_jual', 'pembeli']
    search_fields = ['pembeli__nama']

@admin.register(BagiHasil)
class BagiHasilAdmin(admin.ModelAdmin):
    list_display = ['trip', 'abk', 'nominal', 'sudah_dibayar', 'tgl_bayar']
    list_filter = ['sudah_dibayar']
    search_fields = ['abk__nama']