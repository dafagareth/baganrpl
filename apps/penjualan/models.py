# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.db import models

from apps.tangkap.models import HasilTangkap
from apps.master.models import Pembeli, ABK

class Penjualan(models.Model):
    client_uuid = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    hasil_tangkap = models.ForeignKey(HasilTangkap, on_delete=models.PROTECT, related_name='penjualan')
    pembeli = models.ForeignKey(Pembeli, on_delete=models.PROTECT, related_name='penjualan')
    berat_terjual = models.DecimalField(max_digits=10, decimal_places=2)
    harga_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    tgl_jual = models.DateField()
    catatan = models.TextField(blank=True, null=True)
    foto_bukti = models.ImageField(null=True, blank=True, upload_to='penjualan/bukti/')
    dibuat_pada = models.DateTimeField(auto_now_add=True, null=True)

    def total_nilai(self):
        return self.berat_terjual * self.harga_per_kg

    def __str__(self):
        return f"Jual {self.hasil_tangkap.jenis_ikan} - Rp{self.total_nilai():,.0f}"

    class Meta:
        verbose_name_plural = 'Data Penjualan'
        ordering = ['-tgl_jual']

class BagiHasil(models.Model):
    trip = models.ForeignKey('operasional.Trip', on_delete=models.CASCADE, related_name='bagi_hasil')
    abk = models.ForeignKey(ABK, on_delete=models.PROTECT, related_name='bagi_hasil')
    nominal = models.DecimalField(max_digits=12, decimal_places=2)
    sudah_dibayar = models.BooleanField(default=False)
    tgl_bayar = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Bagi hasil {self.abk.nama} - Trip {self.trip.id}"

    class Meta:
        verbose_name_plural = 'Bagi Hasil ABK'
        unique_together = ('trip', 'abk')