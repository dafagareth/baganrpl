# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.conf import settings
from django.db import models

class Kapal(models.Model):
    STATUS_CHOICES = [
        ('aktif', 'Aktif'),
        ('nonaktif', 'Nonaktif'),
        ('perbaikan', 'Dalam Perbaikan'),
    ]

    nama_kapal = models.CharField(max_length=100)
    jenis = models.CharField(max_length=50)
    kapasitas = models.DecimalField(max_digits=8, decimal_places=2, help_text='Kapasitas dalam ton')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aktif')
    keterangan = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='kapal/', null=True, blank=True)

    def __str__(self):
        return self.nama_kapal

    class Meta:
        verbose_name_plural = 'Kapal'
        ordering = ['nama_kapal']

class ABK(models.Model):
    nama = models.CharField(max_length=100)
    no_hp = models.CharField(max_length=15, blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    aktif = models.BooleanField(default=True)

    def __str__(self):
        return self.nama

    class Meta:
        verbose_name = 'ABK'
        verbose_name_plural = 'Data ABK'
        ordering = ['nama']

class JenisIkan(models.Model):
    nama = models.CharField(max_length=100)
    satuan = models.CharField(max_length=20, default='kg')
    keterangan = models.TextField(blank=True, null=True)
    harga_minimum = models.DecimalField(
        max_digits=12, decimal_places=0,
        null=True, blank=True,
        help_text='Harga minimum per kg (Rp). Kosongkan jika tidak ada batasan.'
    )

    def __str__(self):
        return self.nama

    class Meta:
        verbose_name_plural = 'Jenis Ikan'
        ordering = ['nama']

class Pembeli(models.Model):
    nama = models.CharField(max_length=100)
    alamat = models.TextField(blank=True, null=True)
    no_hp = models.CharField(max_length=15, blank=True, null=True)
    keterangan = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nama

    class Meta:
        verbose_name_plural = 'Data Pembeli'
        ordering = ['nama']

class OperatorKapal(models.Model):
    """Penugasan operator ke kapal — many-to-many eksplisit (owner yang atur)."""
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='kapal_assignments',
        limit_choices_to={'profile__role': 'operator'},
    )
    kapal = models.ForeignKey(
        Kapal,
        on_delete=models.CASCADE,
        related_name='operator_assignments',
    )

    class Meta:
        unique_together = ('operator', 'kapal')
        verbose_name = 'Penugasan Operator'
        verbose_name_plural = 'Penugasan Operator'

    def __str__(self):
        return f"{self.operator.username} → {self.kapal.nama_kapal}"