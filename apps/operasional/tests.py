# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.test import TestCase
from django.utils import timezone
from apps.master.models import Kapal
from apps.operasional.models import Trip
from apps.operasional.forms import TripForm

class TripValidationTestCase(TestCase):
    def setUp(self):
        self.kapal = Kapal.objects.create(
            nama_kapal="Kapal Uji",
            jenis="Bagan",
            kapasitas=10.0,
            status="aktif"
        )
        self.trip_active = Trip.objects.create(
            kapal=self.kapal,
            tgl_berangkat=timezone.now().date(),
            status="berlayar"
        )

    def test_cannot_have_two_sailing_trips_for_same_ship(self):
        # Coba buat trip baru untuk kapal yang sama dengan status 'berlayar'
        form = TripForm(data={
            'kapal': self.kapal.id,
            'tgl_berangkat': timezone.now().date(),
            'status': 'berlayar',
            'catatan': 'Coba dobel berlayar'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertTrue(any("tidak boleh memiliki lebih dari satu trip aktif" in err for err in form.errors['__all__']))

    def test_can_have_sailing_and_persiapan_trips(self):
        # Coba buat trip baru dengan status 'persiapan' (boleh)
        form = TripForm(data={
            'kapal': self.kapal.id,
            'tgl_berangkat': timezone.now().date(),
            'status': 'persiapan',
            'catatan': 'Persiapan boleh dobel'
        })
        self.assertTrue(form.is_valid())

