# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.test import TestCase
from django.utils import timezone
from apps.master.models import Kapal, ABK
from apps.operasional.models import Trip, TripABK
from apps.penjualan.models import BagiHasil
from apps.penjualan.forms import BagiHasilForm, BagiHasilGlobalForm

class BagiHasilValidationTestCase(TestCase):
    def setUp(self):
        self.kapal = Kapal.objects.create(
            nama_kapal="Kapal Uji",
            jenis="Bagan",
            kapasitas=10.0,
            status="aktif"
        )
        self.trip = Trip.objects.create(
            kapal=self.kapal,
            tgl_berangkat=timezone.now().date(),
            status="selesai"
        )
        self.abk1 = ABK.objects.create(nama="ABK Satu", aktif=True)
        self.abk2 = ABK.objects.create(nama="ABK Dua", aktif=True)

        # Tugaskan abk1 ke trip, abk2 tidak ditugaskan
        TripABK.objects.create(trip=self.trip, abk=self.abk1)

    def test_abk_queryset_filtered_by_trip(self):
        # abk dropdown harus berisi abk1, tetapi mengecualikan abk2
        form = BagiHasilForm(trip=self.trip)
        abk_choices = [c[0] for c in form.fields['abk'].choices]
        # Skip empty choice (usually empty string or None)
        abk_choices = [c for c in abk_choices if c]
        self.assertIn(self.abk1.id, abk_choices)
        self.assertNotIn(self.abk2.id, abk_choices)

    def test_cannot_add_bagi_hasil_for_abk_not_on_trip(self):
        # Coba tambah bagi hasil untuk abk2 (tidak ada di trip)
        form = BagiHasilForm(trip=self.trip, data={
            'abk': self.abk2.id,
            'nominal': 500000,
            'sudah_dibayar': True,
            'tgl_bayar': timezone.now().date()
        })
        self.assertFalse(form.is_valid())
        self.assertIn('abk', form.errors)

    def test_cannot_add_duplicate_bagi_hasil_for_same_abk_on_trip(self):
        # Buat bagi hasil pertama
        BagiHasil.objects.create(
            trip=self.trip,
            abk=self.abk1,
            nominal=500000,
            sudah_dibayar=True
        )
        # Coba buat bagi hasil kedua untuk abk1
        form = BagiHasilForm(trip=self.trip, data={
            'abk': self.abk1.id,
            'nominal': 200000,
            'sudah_dibayar': True,
            'tgl_bayar': timezone.now().date()
        })
        self.assertFalse(form.is_valid())
        self.assertIn('abk', form.errors)

