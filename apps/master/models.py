# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
#
# Data master = data acuan yang dipakai berulang di seluruh sistem:
# kapal, ABK (anak buah kapal), jenis ikan, dan pembeli. Data ini jarang
# berubah dan jadi "pilihan" saat operator/owner mengisi trip & penjualan.
from django.conf import settings
from django.db import models


# Satu baris Kapal = satu perahu bagan milik usaha.
class Kapal(models.Model):
    # Daftar pilihan status. Bentuknya (nilai_disimpan_di_db, teks_yang_tampil).
    # Dipakai di field 'status' lewat choices= biar isinya gak sembarangan.
    STATUS_CHOICES = [
        ('aktif', 'Aktif'),
        ('nonaktif', 'Nonaktif'),
        ('perbaikan', 'Dalam Perbaikan'),
    ]

    nama_kapal = models.CharField(max_length=100)
    jenis = models.CharField(max_length=50)
    # DecimalField buat angka yang butuh ketelitian (uang/berat), bukan FloatField.
    kapasitas = models.DecimalField(max_digits=8, decimal_places=2, help_text='Kapasitas dalam ton')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aktif')
    # blank=True boleh kosong di form; null=True boleh NULL di database.
    keterangan = models.TextField(blank=True, null=True)
    # foto disimpan ke folder media/kapal/. butuh library Pillow.
    foto = models.ImageField(upload_to='kapal/', null=True, blank=True)

    # __str__ menentukan teks yang muncul saat objek kapal "dicetak"
    # (mis. di dropdown form atau halaman admin). Tanpa ini tampil "Kapal object (1)".
    def __str__(self):
        return self.nama_kapal

    # Meta = pengaturan tambahan model, bukan kolom database.
    class Meta:
        verbose_name_plural = 'Kapal'   # biar admin gak nulis "Kapals"
        ordering = ['nama_kapal']       # default urut berdasarkan nama


# ABK = anak buah kapal (kru). Dipakai saat memilih siapa ikut di sebuah trip.
class ABK(models.Model):
    nama = models.CharField(max_length=100)
    no_hp = models.CharField(max_length=15, blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    aktif = models.BooleanField(default=True)  # ABK lama bisa dinonaktifkan, bukan dihapus

    def __str__(self):
        return self.nama

    class Meta:
        verbose_name = 'ABK'
        verbose_name_plural = 'Data ABK'
        ordering = ['nama']


# Jenis ikan yang biasa ditangkap (mis. Tongkol, Teri). Dipakai saat input hasil tangkap.
class JenisIkan(models.Model):
    nama = models.CharField(max_length=100)
    satuan = models.CharField(max_length=20, default='kg')
    keterangan = models.TextField(blank=True, null=True)
    # Batas harga jual paling rendah per kg. Dipakai untuk validasi di form penjualan
    # supaya operator gak jual kemurahan. Boleh dikosongkan kalau gak ada aturan.
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


# Pihak yang membeli hasil tangkap (pengepul/tengkulak/pasar).
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


# Tabel penghubung: operator mana boleh pegang kapal mana. Owner yang menentukan.
# Ini relasi many-to-many yang dibuat manual jadi tabel sendiri (bukan ManyToManyField),
# supaya gampang ditambah aturan kalau perlu.
class OperatorKapal(models.Model):
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,            # mengarah ke User bawaan Django
        on_delete=models.CASCADE,            # kalau user dihapus, penugasannya ikut terhapus
        related_name='kapal_assignments',    # cara akses balik: user.kapal_assignments.all()
        limit_choices_to={'profile__role': 'operator'},  # di form hanya tampilkan user ber-role operator
    )
    kapal = models.ForeignKey(
        Kapal,
        on_delete=models.CASCADE,
        related_name='operator_assignments',
    )

    class Meta:
        # satu operator gak boleh didaftarkan dua kali ke kapal yang sama
        unique_together = ('operator', 'kapal')
        verbose_name = 'Penugasan Operator'
        verbose_name_plural = 'Penugasan Operator'

    def __str__(self):
        return f"{self.operator.username} → {self.kapal.nama_kapal}"
