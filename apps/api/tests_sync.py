# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
"""
Test endpoint POST /api/sync/

Skenario yang di-cover:
1. Biaya – synced pertama kali
2. Biaya – duplicate (client_uuid sama, dikirim ulang)
3. Hasil tangkap – synced (trip berstatus 'selesai')
4. Hasil tangkap – failed (trip masih 'berlayar')
5. Penjualan – synced + validasi stok
6. Penjualan – failed oversell (berat diminta > tersedia)
7. Penjualan – duplicate
8. Batch campuran, satu item gagal tidak membatalkan yang lain
9. Payload tanpa client_uuid → failed
10. Tanpa auth → 401
"""
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.master.models import Kapal, JenisIkan, ABK, Pembeli
from apps.operasional.models import Trip, BiayaOperasional
from apps.tangkap.models import HasilTangkap
from apps.penjualan.models import Penjualan

H = {'HTTP_HOST': '127.0.0.1'}
URL = '/api/sync/'

def get_token(user):
    return str(RefreshToken.for_user(user).access_token)

class SyncViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('operator_test', password='pass')
        self.client_api = APIClient()
        self.client_api.credentials(HTTP_AUTHORIZATION='Bearer ' + get_token(self.user))

        # Master data
        self.kapal = Kapal.objects.create(
            nama_kapal='Kapal Test', jenis='Bagan', kapasitas=10)
        self.jenis_ikan = JenisIkan.objects.create(nama='Tuna', satuan='kg')
        self.pembeli = Pembeli.objects.create(nama='Toko Ikan', no_hp='081200000000')

        # Trip selesai
        self.trip_selesai = Trip.objects.create(
            kapal=self.kapal,
            tgl_berangkat='2025-01-10',
            tgl_kembali='2025-01-15',
            status='selesai',
        )
        # Trip masih berlayar
        self.trip_berlayar = Trip.objects.create(
            kapal=self.kapal,
            tgl_berangkat='2025-02-01',
            status='berlayar',
        )

        # HasilTangkap dengan stok 100 kg (trip selesai)
        self.ht = HasilTangkap.objects.create(
            trip=self.trip_selesai,
            jenis_ikan=self.jenis_ikan,
            berat_kg=100,
            kondisi='segar',
        )

    def post(self, operations):
        return self.client_api.post(URL, {'operations': operations},
                                    format='json', **H)

    def test_biaya_synced(self):
        uid = str(uuid.uuid4())
        resp = self.post([{
            'client_uuid': uid,
            'type': 'biaya',
            'data': {
                'trip': self.trip_selesai.id,
                'kategori': 'bbm',
                'jumlah': '500000',
                'keterangan': 'Solar 50L',
            },
        }])
        self.assertEqual(resp.status_code, 200)
        r = resp.data['results'][0]
        self.assertEqual(r['status'], 'synced')
        self.assertEqual(r['client_uuid'], uid)
        self.assertIn('id', r)
        self.assertTrue(BiayaOperasional.objects.filter(client_uuid=uid).exists())

    def test_biaya_duplicate(self):
        uid = str(uuid.uuid4())
        payload = [{
            'client_uuid': uid,
            'type': 'biaya',
            'data': {
                'trip': self.trip_selesai.id,
                'kategori': 'es',
                'jumlah': '200000',
            },
        }]
        self.post(payload)          # kiriman pertama
        resp = self.post(payload)   # kiriman ulang
        r = resp.data['results'][0]
        self.assertEqual(r['status'], 'duplicate')
        # Hanya 1 record di DB
        self.assertEqual(BiayaOperasional.objects.filter(client_uuid=uid).count(), 1)

    def test_hasil_tangkap_synced(self):
        uid = str(uuid.uuid4())
        resp = self.post([{
            'client_uuid': uid,
            'type': 'hasil_tangkap',
            'data': {
                'trip': self.trip_selesai.id,
                'jenis_ikan': self.jenis_ikan.id,
                'berat_kg': '80',
                'kondisi': 'segar',
            },
        }])
        r = resp.data['results'][0]
        self.assertEqual(r['status'], 'synced')
        self.assertTrue(HasilTangkap.objects.filter(client_uuid=uid).exists())

    def test_hasil_tangkap_trip_berlayar(self):
        uid = str(uuid.uuid4())
        resp = self.post([{
            'client_uuid': uid,
            'type': 'hasil_tangkap',
            'data': {
                'trip': self.trip_berlayar.id,
                'jenis_ikan': self.jenis_ikan.id,
                'berat_kg': '50',
                'kondisi': 'segar',
            },
        }])
        r = resp.data['results'][0]
        self.assertEqual(r['status'], 'failed')
        self.assertIn('selesai', r['error'])

    def test_penjualan_synced(self):
        uid = str(uuid.uuid4())
        resp = self.post([{
            'client_uuid': uid,
            'type': 'penjualan',
            'data': {
                'hasil_tangkap': self.ht.id,
                'pembeli': self.pembeli.id,
                'berat_terjual': '30',
                'harga_per_kg': '50000',
                'tgl_jual': '2025-01-16',
            },
        }])
        r = resp.data['results'][0]
        self.assertEqual(r['status'], 'synced')
        self.assertTrue(Penjualan.objects.filter(client_uuid=uid).exists())
        # Stok berkurang
        self.ht.refresh_from_db()
        self.assertEqual(self.ht.berat_tersedia, 70)

    def test_penjualan_oversell(self):
        uid = str(uuid.uuid4())
        resp = self.post([{
            'client_uuid': uid,
            'type': 'penjualan',
            'data': {
                'hasil_tangkap': self.ht.id,
                'pembeli': self.pembeli.id,
                'berat_terjual': '999',        # >> 100 kg tersedia
                'harga_per_kg': '50000',
                'tgl_jual': '2025-01-16',
            },
        }])
        r = resp.data['results'][0]
        self.assertEqual(r['status'], 'failed')
        self.assertIn('Stok tidak cukup', r['error'])
        self.assertFalse(Penjualan.objects.filter(client_uuid=uid).exists())

    def test_penjualan_duplicate(self):
        uid = str(uuid.uuid4())
        payload = [{
            'client_uuid': uid,
            'type': 'penjualan',
            'data': {
                'hasil_tangkap': self.ht.id,
                'pembeli': self.pembeli.id,
                'berat_terjual': '10',
                'harga_per_kg': '40000',
                'tgl_jual': '2025-01-16',
            },
        }]
        self.post(payload)
        resp = self.post(payload)
        r = resp.data['results'][0]
        self.assertEqual(r['status'], 'duplicate')
        self.assertEqual(Penjualan.objects.filter(client_uuid=uid).count(), 1)
        # Stok hanya berkurang 10, bukan 20
        self.assertEqual(self.ht.berat_tersedia, 90)

    def test_batch_mixed(self):
        """Satu item gagal (oversell) tidak membatalkan item lain."""
        uid_ok = str(uuid.uuid4())
        uid_fail = str(uuid.uuid4())
        resp = self.post([
            {
                'client_uuid': uid_ok,
                'type': 'biaya',
                'data': {
                    'trip': self.trip_selesai.id,
                    'kategori': 'logistik',
                    'jumlah': '150000',
                },
            },
            {
                'client_uuid': uid_fail,
                'type': 'penjualan',
                'data': {
                    'hasil_tangkap': self.ht.id,
                    'pembeli': self.pembeli.id,
                    'berat_terjual': '9999',
                    'harga_per_kg': '50000',
                    'tgl_jual': '2025-01-16',
                },
            },
        ])
        results = {r['client_uuid']: r for r in resp.data['results']}
        self.assertEqual(results[uid_ok]['status'], 'synced')
        self.assertEqual(results[uid_fail]['status'], 'failed')

    def test_missing_client_uuid(self):
        resp = self.post([{
            'type': 'biaya',
            'data': {'trip': self.trip_selesai.id, 'kategori': 'bbm', 'jumlah': '100'},
        }])
        r = resp.data['results'][0]
        self.assertEqual(r['status'], 'failed')
        self.assertIn('client_uuid', r['error'])

    def test_unauthenticated(self):
        anon = APIClient()
        resp = anon.post(URL, {'operations': []}, format='json', **H)
        self.assertEqual(resp.status_code, 401)
