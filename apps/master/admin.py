# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.contrib import admin

# Register your models here.

from .models import Kapal, ABK, JenisIkan, Pembeli

@admin.register(Kapal)
class KapalAdmin(admin.ModelAdmin):
    list_display = ['nama_kapal', 'jenis', 'kapasitas', 'status']
    list_filter = ['status']
    search_fields = ['nama_kapal']

@admin.register(ABK)
class ABKAdmin(admin.ModelAdmin):
    list_display = ['nama', 'no_hp', 'aktif']
    list_filter = ['aktif']
    search_fields = ['nama']

@admin.register(JenisIkan)
class JenisIkanAdmin(admin.ModelAdmin):
    list_display = ['nama', 'satuan']
    search_fields = ['nama']

@admin.register(Pembeli)
class PembeliAdmin(admin.ModelAdmin):
    list_display = ['nama', 'no_hp', 'alamat']
    search_fields = ['nama']