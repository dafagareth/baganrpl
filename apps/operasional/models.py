# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.conf import settings
from django.db import models
from apps.master.models import Kapal, ABK

class Trip(models.Model):
    STATUS_CHOICES = [
        ('persiapan', 'Persiapan'),
        ('berlayar', 'Sedang Berlayar'),
        ('selesai', 'Selesai'),
        ('batal', 'Dibatalkan'),
    ]

    kapal = models.ForeignKey(Kapal, on_delete=models.PROTECT, related_name='trips')
    tgl_berangkat = models.DateField()
    tgl_kembali = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='persiapan')
    catatan = models.TextField(blank=True, null=True)
    is_laporan_locked = models.BooleanField(default=False)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    dibuat_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trips_dibuat',
    )
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip {self.kapal} - {self.tgl_berangkat}"

    def total_biaya_operasional(self):
        return self.biaya_operasional.aggregate(
            total=models.Sum('jumlah')
        )['total'] or 0

    def total_pendapatan(self):
        from apps.penjualan.models import Penjualan
        return Penjualan.objects.filter(
            hasil_tangkap__trip=self
        ).aggregate(
            total=models.Sum(models.F('berat_terjual') * models.F('harga_per_kg'))
        )['total'] or 0

    def laba_kotor(self):
        return self.total_pendapatan() - self.total_biaya_operasional()

    def total_bagi_hasil(self):
        return self.bagi_hasil.filter(sudah_dibayar=True).aggregate(
            total=models.Sum('nominal')
        )['total'] or 0

    def laba_bersih(self):
        return self.laba_kotor() - self.total_bagi_hasil()

    class Meta:
        verbose_name_plural = 'Data Trip'
        ordering = ['-dibuat_pada', '-id']

class TripABK(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='trip_abk')
    abk = models.ForeignKey(ABK, on_delete=models.PROTECT, related_name='trip_abk')

    def __str__(self):
        return f"{self.abk.nama} - {self.trip}"

    class Meta:
        unique_together = ('trip', 'abk')
        verbose_name = 'ABK Trip'

class BiayaOperasional(models.Model):
    KATEGORI_CHOICES = [
        ('bbm', 'BBM'),
        ('es', 'Es Balok'),
        ('logistik', 'Logistik / Perbekalan'),
        ('perawatan', 'Perawatan Alat'),
        ('lainnya', 'Lainnya'),
    ]

    client_uuid = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='biaya_operasional')
    kategori = models.CharField(max_length=20, choices=KATEGORI_CHOICES)
    jumlah = models.DecimalField(max_digits=12, decimal_places=2)
    keterangan = models.CharField(max_length=200, blank=True, null=True)
    foto_bukti = models.ImageField(upload_to='biaya/', null=True, blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.get_kategori_display()} - Rp{self.jumlah:,.0f}"

    class Meta:
        verbose_name_plural = 'Biaya Operasional'