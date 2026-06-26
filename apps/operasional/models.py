# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
#
# Inti aplikasi: Trip (satu kali melaut) beserta data yang menempel padanya,
# yaitu ABK yang ikut (TripABK) dan biaya selama trip (BiayaOperasional).
# Hasil tangkap & penjualan ada di app lain tapi tetap menunjuk ke Trip.
from django.conf import settings
from django.db import models
from apps.master.models import Kapal, ABK


# Satu Trip = satu perjalanan melaut dari berangkat sampai kembali.
class Trip(models.Model):
    # Alur status normal: persiapan -> berlayar -> selesai. 'batal' kalau dibatalkan.
    STATUS_CHOICES = [
        ('persiapan', 'Persiapan'),
        ('berlayar', 'Sedang Berlayar'),
        ('selesai', 'Selesai'),
        ('batal', 'Dibatalkan'),
    ]

    # PROTECT: kapal gak bisa dihapus selama masih punya trip (jaga histori).
    kapal = models.ForeignKey(Kapal, on_delete=models.PROTECT, related_name='trips')
    tgl_berangkat = models.DateField()
    tgl_kembali = models.DateField(blank=True, null=True)   # diisi pas trip selesai
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='persiapan')
    catatan = models.TextField(blank=True, null=True)
    # Kalau True, data trip dikunci dan gak bisa diedit lagi (owner yang mengunci).
    is_laporan_locked = models.BooleanField(default=False)
    # Titik koordinat lokasi (opsional), diisi dari GPS HP operator.
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    dibuat_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,   # kalau user dihapus, trip tetap ada tapi kolom ini jadi kosong
        null=True, blank=True,
        related_name='trips_dibuat',
    )
    dibuat_pada = models.DateTimeField(auto_now_add=True)  # otomatis diisi waktu objek pertama dibuat

    def __str__(self):
        return f"Trip {self.kapal} - {self.tgl_berangkat}"

    # ---- Method hitung uang. Bukan kolom database, dihitung saat dipanggil. ----

    # Jumlahkan semua biaya operasional milik trip ini.
    # self.biaya_operasional = akses balik dari related_name di model BiayaOperasional.
    # aggregate(Sum(...)) menyuruh database yang menjumlahkan (lebih cepat dari loop Python).
    # "or 0" jaga-jaga kalau belum ada biaya (hasilnya None).
    def total_biaya_operasional(self):
        return self.biaya_operasional.aggregate(
            total=models.Sum('jumlah')
        )['total'] or 0

    # Total uang masuk = jumlah dari (berat_terjual x harga_per_kg) tiap penjualan di trip ini.
    # F() dipakai supaya perkalian antar-kolom dikerjakan di sisi database.
    # import-nya di dalam fungsi untuk menghindari circular import (penjualan -> tangkap -> operasional).
    def total_pendapatan(self):
        from apps.penjualan.models import Penjualan
        return Penjualan.objects.filter(
            hasil_tangkap__trip=self   # ikuti relasi: Penjualan -> HasilTangkap -> Trip
        ).aggregate(
            total=models.Sum(models.F('berat_terjual') * models.F('harga_per_kg'))
        )['total'] or 0

    # Laba kotor = pendapatan dikurangi biaya operasional (belum dikurangi bagi hasil ABK).
    def laba_kotor(self):
        return self.total_pendapatan() - self.total_biaya_operasional()

    # Total bagi hasil yang BENAR-BENAR sudah dibayar ke ABK (yang belum dibayar tidak dihitung).
    def total_bagi_hasil(self):
        return self.bagi_hasil.filter(sudah_dibayar=True).aggregate(
            total=models.Sum('nominal')
        )['total'] or 0

    # Laba bersih = laba kotor dikurangi bagi hasil yang sudah dibayar.
    def laba_bersih(self):
        return self.laba_kotor() - self.total_bagi_hasil()

    class Meta:
        verbose_name_plural = 'Data Trip'
        ordering = ['-dibuat_pada', '-id']  # tanda minus = urut menurun (terbaru di atas)


# Penghubung Trip <-> ABK: mencatat ABK mana saja yang ikut di sebuah trip.
class TripABK(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='trip_abk')   # ikut terhapus kalau trip dihapus
    abk = models.ForeignKey(ABK, on_delete=models.PROTECT, related_name='trip_abk')     # ABK dilindungi dari penghapusan

    def __str__(self):
        return f"{self.abk.nama} - {self.trip}"

    class Meta:
        unique_together = ('trip', 'abk')   # satu ABK gak bisa dimasukkan dua kali ke trip yang sama
        verbose_name = 'ABK Trip'


# Pengeluaran selama satu trip (BBM, es, perbekalan, dll).
class BiayaOperasional(models.Model):
    KATEGORI_CHOICES = [
        ('bbm', 'BBM'),
        ('es', 'Es Balok'),
        ('logistik', 'Logistik / Perbekalan'),
        ('perawatan', 'Perawatan Alat'),
        ('lainnya', 'Lainnya'),
    ]

    # ID unik dari aplikasi (sisa fitur sinkronisasi offline mobile). unique biar
    # kiriman ganda gak bikin data dobel. editable=False = gak muncul di form.
    client_uuid = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='biaya_operasional')
    kategori = models.CharField(max_length=20, choices=KATEGORI_CHOICES)
    jumlah = models.DecimalField(max_digits=12, decimal_places=2)
    keterangan = models.CharField(max_length=200, blank=True, null=True)
    foto_bukti = models.ImageField(upload_to='biaya/', null=True, blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        # get_kategori_display() = teks panjang dari choices (mis. 'bbm' -> 'BBM').
        # bawaan Django: get_<namafield>_display().
        return f"{self.get_kategori_display()} - Rp{self.jumlah:,.0f}"

    class Meta:
        verbose_name_plural = 'Biaya Operasional'
