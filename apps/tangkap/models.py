# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.db import models

from apps.operasional.models import Trip
from apps.master.models import JenisIkan

class HasilTangkap(models.Model):
    KONDISI_CHOICES = [
        ('segar', 'Segar'),
        ('beku', 'Beku'),
        ('olahan', 'Olahan'),
    ]

    client_uuid = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='hasil_tangkap')
    jenis_ikan = models.ForeignKey(JenisIkan, on_delete=models.PROTECT, related_name='hasil_tangkap')
    berat_kg = models.DecimalField(max_digits=10, decimal_places=2)
    kondisi = models.CharField(max_length=10, choices=KONDISI_CHOICES, default='segar')
    catatan = models.TextField(blank=True, null=True)
    foto_bukti = models.ImageField(null=True, blank=True, upload_to='tangkap/bukti/')
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True, null=True)

    @property
    def berat_tersedia(self):
        terjual = self.penjualan.aggregate(total=models.Sum('berat_terjual'))['total'] or 0
        return self.berat_kg - terjual

    def __str__(self):
        return f"{self.jenis_ikan.nama} - Sisa {self.berat_tersedia:g}kg dari {self.berat_kg:g}kg ({self.trip})"

    class Meta:
        verbose_name_plural = 'Hasil Tangkap'