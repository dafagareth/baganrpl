# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.contrib import admin

# Register your models here.
from .models import HasilTangkap

@admin.register(HasilTangkap)
class HasilTangkapAdmin(admin.ModelAdmin):
    list_display = ['trip', 'jenis_ikan', 'berat_kg', 'kondisi']
    list_filter = ['kondisi', 'jenis_ikan']
    search_fields = ['trip__kapal__nama_kapal', 'jenis_ikan__nama']