# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
"""Isi database dengan data dummy realistis untuk demo usaha bagan.

Pakai:  python manage.py seed_dummy --flush
- --flush  : hapus dulu semua data operasional + master (akun TIDAK dihapus).
Membuat akun owner/owner dan operator/operator, master data, lalu trip mingguan
sejak Januari 2025 dengan variasi nyata: kadang minggu dilewati (kapal rusak /
cuaca), kadang trip pulang tanpa hasil tangkap.
"""
import random
from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.master.models import Kapal, ABK, JenisIkan, Pembeli
from apps.operasional.models import Trip, TripABK, BiayaOperasional
from apps.tangkap.models import HasilTangkap
from apps.penjualan.models import Penjualan, BagiHasil
from apps.api.models import UserProfile

User = get_user_model()

IKAN = [
    ('Teri', 25000), ('Tongkol', 18000), ('Kembung', 22000),
    ('Selar', 16000), ('Cumi-cumi', 35000), ('Tenggiri', 40000),
]
ABK_NAMA = ['Imet', 'Buyung', 'Udin', 'Sutan', 'Joni', 'Asep']
PEMBELI_NAMA = ['Pengepul Pasar Bungus', 'UD Laut Jaya', 'Restoran Sari Laut', 'Koperasi Nelayan Sejahtera']
BIAYA_POOL = [
    ('Solar / BBM', 200000, 600000),
    ('Es balok', 80000, 200000),
    ('Perbekalan & konsumsi', 100000, 300000),
    ('Oli mesin', 50000, 150000),
    ('Rokok & ransum awak', 60000, 150000),
]


def _aware(d, hour=8):
    return timezone.make_aware(datetime.combine(d, time(hour, 0)))


# Management command = skrip yang dijalankan lewat `python manage.py <nama>`. Caranya:
# bikin kelas bernama Command turunan BaseCommand, lalu tulis logikanya di method handle().
# Nama perintah = nama file ini (seed_dummy).
class Command(BaseCommand):
    help = 'Isi data dummy realistis untuk demo usaha bagan.'

    # daftarkan opsi --flush. action='store_true' artinya opsi tanpa nilai (ada/tidak).
    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true',
                            help='Hapus semua data operasional + master dulu (akun tidak dihapus).')

    # @transaction.atomic: semua perubahan di handle() dianggap satu paket. Kalau ada yang
    # gagal di tengah, SEMUA dibatalkan (database tidak setengah jadi).
    @transaction.atomic
    def handle(self, *args, **opts):
        # seed angka tetap (20260101) supaya "acak"-nya selalu sama tiap dijalankan.
        # Jadi data dummy bisa dibuat ulang persis sama (deterministik).
        rnd = random.Random(20260101)

        if opts['flush']:
            BagiHasil.objects.all().delete()
            Penjualan.objects.all().delete()
            HasilTangkap.objects.all().delete()
            BiayaOperasional.objects.all().delete()
            TripABK.objects.all().delete()
            Trip.objects.all().delete()
            Kapal.objects.all().delete()
            ABK.objects.all().delete()
            JenisIkan.objects.all().delete()
            Pembeli.objects.all().delete()
            self.stdout.write('Data lama dihapus (akun dibiarkan).')

        # ── Akun owner & operator ───────────────────────────────
        # get_or_create: ambil user 'owner' kalau sudah ada, kalau belum buat baru.
        # Mengembalikan (objek, dibuat_atau_tidak); kita abaikan flag kedua dengan _.
        owner, _ = User.objects.get_or_create(
            username='owner', defaults={'first_name': 'Pemilik Usaha'})
        # password tidak boleh diisi mentah; set_password() yang meng-hash-nya dengan aman.
        owner.set_password('owner'); owner.save()
        UserProfile.objects.update_or_create(user=owner, defaults={'role': 'owner'})

        operator, _ = User.objects.get_or_create(
            username='operator', defaults={'first_name': 'Operator Kapal'})
        operator.set_password('operator'); operator.save()
        UserProfile.objects.update_or_create(user=operator, defaults={'role': 'operator'})

        # ── Master ──────────────────────────────────────────────
        kapal_list = [
            Kapal.objects.create(nama_kapal='Bagan Jaya I', jenis='Bagan', kapasitas=5, status='aktif'),
            Kapal.objects.create(nama_kapal='Bagan Jaya II', jenis='Bagan', kapasitas=7, status='aktif'),
        ]
        abk_list = [ABK.objects.create(nama=n, no_hp='0812000000' + str(i), aktif=True)
                    for i, n in enumerate(ABK_NAMA, 1)]
        ikan_list = [JenisIkan.objects.create(nama=n, satuan='kg', harga_minimum=h) for n, h in IKAN]
        pembeli_list = [Pembeli.objects.create(nama=n, no_hp='0813000000' + str(i))
                        for i, n in enumerate(PEMBELI_NAMA, 1)]

        # ── Trip mingguan sejak Jan 2025 ────────────────────────
        # Bangun daftar tanggal Senin tiap minggu dari awal 2025 sampai hari ini,
        # lalu untuk tiap minggu dibuatkan satu trip (dengan variasi di loop bawah).
        start = date(2025, 1, 6)          # Senin pertama
        end = date.today()
        weeks = []
        d = start
        while d <= end:
            weeks.append(d)
            d += timedelta(days=7)        # maju 7 hari = minggu berikutnya

        n_trip = n_skip = n_nihil = 0
        for i, wk in enumerate(weeks):
            is_last = (i == len(weeks) - 1)
            # ~15% minggu dilewati (kapal rusak / cuaca) — kecuali minggu terakhir
            if not is_last and rnd.random() < 0.15:
                n_skip += 1
                continue

            kapal = rnd.choice(kapal_list)
            berangkat = wk + timedelta(days=rnd.randint(0, 1))
            kembali = berangkat + timedelta(days=rnd.randint(1, 2))

            if is_last:
                trip = Trip.objects.create(
                    kapal=kapal, tgl_berangkat=berangkat, tgl_kembali=None,
                    status='berlayar', is_laporan_locked=False, dibuat_oleh=operator)
            else:
                trip = Trip.objects.create(
                    kapal=kapal, tgl_berangkat=berangkat, tgl_kembali=kembali,
                    status='selesai', is_laporan_locked=True, dibuat_oleh=operator)
            Trip.objects.filter(pk=trip.pk).update(dibuat_pada=_aware(berangkat))
            n_trip += 1

            # ABK 3-4 orang
            for abk in rnd.sample(abk_list, rnd.randint(3, 4)):
                TripABK.objects.create(trip=trip, abk=abk)

            # Biaya 2-4 barang
            for nama, lo, hi in rnd.sample(BIAYA_POOL, rnd.randint(2, 4)):
                b = BiayaOperasional.objects.create(
                    trip=trip, kategori='lainnya', keterangan=nama,
                    jumlah=rnd.randrange(lo, hi, 5000))
                BiayaOperasional.objects.filter(pk=b.pk).update(dibuat_pada=_aware(berangkat))

            if is_last:
                continue  # trip aktif: belum ada tangkap/jual/bagi hasil

            # ~10% trip pulang tanpa hasil (cuaca buruk)
            if rnd.random() < 0.10:
                n_nihil += 1
                continue

            # Hasil tangkap 1-3 jenis
            for ikan in rnd.sample(ikan_list, rnd.randint(1, 3)):
                berat = rnd.randrange(15, 220, 5)
                ht = HasilTangkap.objects.create(
                    trip=trip, jenis_ikan=ikan, berat_kg=berat,
                    kondisi=rnd.choice(['segar', 'segar', 'beku']))
                HasilTangkap.objects.filter(pk=ht.pk).update(dibuat_pada=_aware(kembali))

                # Jual 80-100% ke pembeli, harga >= minimum
                terjual = round(berat * rnd.uniform(0.8, 1.0), 1)
                harga = int(float(ikan.harga_minimum) * rnd.uniform(1.0, 1.4) // 500 * 500)
                pj = Penjualan.objects.create(
                    hasil_tangkap=ht, pembeli=rnd.choice(pembeli_list),
                    berat_terjual=terjual, harga_per_kg=harga, tgl_jual=kembali)
                Penjualan.objects.filter(pk=pj.pk).update(dibuat_pada=_aware(kembali))

            # Bagi hasil per ABK (kebijakan owner; sebagian sudah dibayar)
            for ta in TripABK.objects.filter(trip=trip):
                sudah = rnd.random() < 0.7
                BagiHasil.objects.create(
                    trip=trip, abk=ta.abk, nominal=rnd.randrange(100000, 500000, 25000),
                    sudah_dibayar=sudah, tgl_bayar=(kembali + timedelta(days=2)) if sudah else None)

        self.stdout.write(self.style.SUCCESS(
            f'Selesai. Trip dibuat: {n_trip} (skip {n_skip} minggu, {n_nihil} trip nihil). '
            f'Akun: owner/owner & operator/operator.'))
