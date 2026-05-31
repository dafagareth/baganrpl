# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
"""
Test endpoint bagi hasil owner

Skenario:
1. GET /api/trips/{id}/          → detail trip + ringkasan keuangan
2. GET /api/trips/{id}/bagi-hasil/ → list (operator boleh baca)
3. POST /api/trips/{id}/bagi-hasil/ → owner bisa tambah
4. POST oleh operator → 403
5. POST ABK tidak ada di trip → 400
6. PATCH /api/bagi-hasil/{id}/   → owner ubah nominal / tandai bayar
7. PATCH oleh operator → 403
8. DELETE /api/bagi-hasil/{id}/  → owner hapus
9. Tanpa auth → 401
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.master.models import Kapal, ABK, JenisIkan, Pembeli
from apps.operasional.models import Trip, TripABK
from apps.tangkap.models import HasilTangkap
from apps.penjualan.models import Penjualan, BagiHasil
from apps.api.models import UserProfile

H = {'HTTP_HOST': '127.0.0.1'}

def token(user):
    return str(RefreshToken.for_user(user).access_token)

def auth(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION='Bearer ' + token(user))
    return c

class BagiHasilAPITest(TestCase):
    def setUp(self):
        # Users
        self.owner_user = User.objects.create_user('owner1', password='pass')
        UserProfile.objects.filter(user=self.owner_user).update(role='owner')

        self.operator_user = User.objects.create_user('operator1', password='pass')
        UserProfile.objects.filter(user=self.operator_user).update(role='operator')

        self.owner = auth(self.owner_user)
        self.operator = auth(self.operator_user)

        # Master
        self.kapal = Kapal.objects.create(
            nama_kapal='KM Sejahtera', jenis='Bagan', kapasitas=15)
        self.abk1 = ABK.objects.create(nama='Budi')
        self.abk2 = ABK.objects.create(nama='Candra')
        self.abk_luar = ABK.objects.create(nama='Asing')  # tidak ada di trip

        # Trip selesai
        self.trip = Trip.objects.create(
            kapal=self.kapal,
            tgl_berangkat='2025-03-01',
            tgl_kembali='2025-03-07',
            status='selesai',
        )
        TripABK.objects.create(trip=self.trip, abk=self.abk1)
        TripABK.objects.create(trip=self.trip, abk=self.abk2)

        # HasilTangkap + Penjualan supaya keuangan ada isinya
        jenis_ikan = JenisIkan.objects.create(nama='Kerapu', satuan='kg')
        pembeli = Pembeli.objects.create(nama='Pak Tono')
        ht = HasilTangkap.objects.create(
            trip=self.trip, jenis_ikan=jenis_ikan, berat_kg=200, kondisi='segar')
        Penjualan.objects.create(
            hasil_tangkap=ht, pembeli=pembeli,
            berat_terjual=100, harga_per_kg=60000, tgl_jual='2025-03-08')

    def test_trip_detail(self):
        resp = self.owner.get(f'/api/trips/{self.trip.id}/', **H)
        self.assertEqual(resp.status_code, 200)
        d = resp.data
        self.assertEqual(d['status'], 'selesai')
        self.assertIn('total_pendapatan', d)
        self.assertIn('laba_kotor', d)
        self.assertIn('abk_list', d)
        self.assertEqual(len(d['abk_list']), 2)
        self.assertEqual(d['total_pendapatan'], 100 * 60000)

    def test_list_bagi_hasil_operator_bisa_baca(self):
        BagiHasil.objects.create(trip=self.trip, abk=self.abk1, nominal=500000)
        resp = self.operator.get(f'/api/trips/{self.trip.id}/bagi-hasil/', **H)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_owner_tambah_bagi_hasil(self):
        resp = self.owner.post(
            f'/api/trips/{self.trip.id}/bagi-hasil/',
            {'abk': self.abk1.id, 'nominal': '750000'},
            format='json', **H,
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['abk_nama'], 'Budi')
        self.assertEqual(float(resp.data['nominal']), 750000)
        self.assertFalse(resp.data['sudah_dibayar'])

    def test_operator_tidak_bisa_tambah(self):
        resp = self.operator.post(
            f'/api/trips/{self.trip.id}/bagi-hasil/',
            {'abk': self.abk1.id, 'nominal': '500000'},
            format='json', **H,
        )
        self.assertEqual(resp.status_code, 403)

    def test_abk_tidak_ada_di_trip(self):
        resp = self.owner.post(
            f'/api/trips/{self.trip.id}/bagi-hasil/',
            {'abk': self.abk_luar.id, 'nominal': '500000'},
            format='json', **H,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('abk', resp.data)

    def test_owner_patch_bagi_hasil(self):
        bh = BagiHasil.objects.create(
            trip=self.trip, abk=self.abk2, nominal=300000)
        resp = self.owner.patch(
            f'/api/bagi-hasil/{bh.id}/',
            {'nominal': '400000', 'sudah_dibayar': True, 'tgl_bayar': '2025-03-10'},
            format='json', **H,
        )
        self.assertEqual(resp.status_code, 200)
        bh.refresh_from_db()
        self.assertEqual(float(bh.nominal), 400000)
        self.assertTrue(bh.sudah_dibayar)

    def test_operator_tidak_bisa_patch(self):
        bh = BagiHasil.objects.create(
            trip=self.trip, abk=self.abk1, nominal=200000)
        resp = self.operator.patch(
            f'/api/bagi-hasil/{bh.id}/',
            {'nominal': '999999'},
            format='json', **H,
        )
        self.assertEqual(resp.status_code, 403)

    def test_owner_delete_bagi_hasil(self):
        bh = BagiHasil.objects.create(
            trip=self.trip, abk=self.abk1, nominal=100000)
        resp = self.owner.delete(f'/api/bagi-hasil/{bh.id}/', **H)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(BagiHasil.objects.filter(pk=bh.id).exists())

    def test_unauthenticated(self):
        anon = APIClient()
        resp = anon.get(f'/api/trips/{self.trip.id}/bagi-hasil/', **H)
        self.assertEqual(resp.status_code, 401)
