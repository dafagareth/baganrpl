# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.contrib import admin

# Register your models here.
from .models import Trip, TripABK, BiayaOperasional

class TripABKInline(admin.TabularInline):
    model = TripABK
    extra = 1

class BiayaOperasionalInline(admin.TabularInline):
    model = BiayaOperasional
    extra = 1

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'kapal', 'tgl_berangkat', 'tgl_kembali', 'status']
    list_filter = ['status', 'kapal']
    search_fields = ['kapal__nama_kapal']
    inlines = [TripABKInline, BiayaOperasionalInline]