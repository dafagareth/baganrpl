# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
"""
Test FCM push notification & integrasi dengan sync endpoint.

Skenario:
1. notify_owners: simpan Notification DB untuk semua owner
2. notify_owners: kirim FCM ke token owner (mock send)
3. notify_owners: token kadaluarsa dihapus dari DB (UnregisteredError)
4. notify_owners: FCM tidak dikonfigurasi → Notification DB tetap dibuat
5. Sync sukses → notify_owners dipanggil (terintegrasi end-to-end)
6. Sync duplikat semua → notify_owners TIDAK dipanggil
"""
import uuid
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.master.models import Kapal, JenisIkan
from apps.operasional.models import Trip
from apps.api.models import DeviceToken, Notification, UserProfile
from apps.api import fcm as fcm_module

H = {'HTTP_HOST': '127.0.0.1'}
NO_FCM = {'FIREBASE_CREDENTIALS_PATH': ''}

def token(user):
    return str(RefreshToken.for_user(user).access_token)

class FCMNotifyOwnersTest(TestCase):
    """Unit test notify_owners() langsung."""

    def setUp(self):
        # Dua owner
        self.o1 = User.objects.create_user('owner_a', password='x')
        self.o2 = User.objects.create_user('owner_b', password='x')
        UserProfile.objects.filter(user=self.o1).update(role='owner')
        UserProfile.objects.filter(user=self.o2).update(role='owner')

        # Satu operator (bukan owner)
        self.op = User.objects.create_user('oper', password='x')

        # Token device
        self.tok1 = DeviceToken.objects.create(user=self.o1, token='TOKEN_A')
        self.tok2 = DeviceToken.objects.create(user=self.o2, token='TOKEN_B')

    def tearDown(self):
        # Reset state global _initialized setiap test
        fcm_module._initialized = False

    @override_settings(**NO_FCM)
    def test_notification_db_dibuat(self):
        notifs = fcm_module.notify_owners(
            event='sync', judul='Ada data baru', pesan='2 operasi masuk')
        self.assertEqual(len(notifs), 2)
        self.assertEqual(Notification.objects.count(), 2)
        users_notified = set(Notification.objects.values_list('user_id', flat=True))
        self.assertIn(self.o1.id, users_notified)
        self.assertIn(self.o2.id, users_notified)
        # Operator TIDAK dapat notif
        self.assertNotIn(self.op.id, users_notified)

    @override_settings(FIREBASE_CREDENTIALS_PATH='/fake/path.json')
    def test_fcm_send_dipanggil(self):
        # Patch init Firebase & messaging.send
        with patch.object(fcm_module, '_init_firebase', return_value=True), \
             patch('apps.api.fcm.messaging') as mock_msg:
            mock_msg.send = MagicMock(return_value='projects/x/messages/1')
            mock_msg.UnregisteredError = Exception  # supaya except-nya tidak tersentuh

            fcm_module.notify_owners(
                event='sync', judul='Test push', pesan='Isi pesan')

        # Cek token via kwargs di konstruktor Message (bukan .token dari MagicMock)
        calls = mock_msg.Message.call_args_list
        called_tokens = [c.kwargs['token'] for c in calls]
        self.assertIn('TOKEN_A', called_tokens)
        self.assertIn('TOKEN_B', called_tokens)
        self.assertEqual(mock_msg.send.call_count, 2)

    @override_settings(FIREBASE_CREDENTIALS_PATH='/fake/path.json')
    def test_token_kadaluarsa_dihapus(self):
        class FakeUnregistered(Exception):
            pass

        # Buat objek Message yang menyimpan token-nya
        class FakeMessage:
            def __init__(self, notification=None, data=None, token=None):
                self.token = token

        def fake_send(msg):
            if msg.token == 'TOKEN_A':
                raise FakeUnregistered()
            return 'ok'

        with patch.object(fcm_module, '_init_firebase', return_value=True), \
             patch('apps.api.fcm.messaging') as mock_msg:
            mock_msg.UnregisteredError = FakeUnregistered
            mock_msg.send = MagicMock(side_effect=fake_send)
            mock_msg.Message = FakeMessage
            mock_msg.Notification = MagicMock()

            fcm_module.notify_owners(event='x', judul='T', pesan='P')

        # TOKEN_A harus sudah hilang dari DB
        self.assertFalse(DeviceToken.objects.filter(token='TOKEN_A').exists())
        self.assertTrue(DeviceToken.objects.filter(token='TOKEN_B').exists())

    @override_settings(**NO_FCM)
    def test_tanpa_firebase_db_tetap_dibuat(self):
        with patch.object(fcm_module, '_send_to_tokens', return_value=(0, 0)):
            notifs = fcm_module.notify_owners(event='e', judul='J', pesan='P')
        self.assertEqual(Notification.objects.count(), 2)

class FCMSyncIntegrationTest(TestCase):
    """Integrasi: sync endpoint → notify_owners."""

    def setUp(self):
        fcm_module._initialized = False

        self.operator_user = User.objects.create_user('sync_op', password='x')
        self.owner_user = User.objects.create_user('sync_own', password='x')
        UserProfile.objects.filter(user=self.owner_user).update(role='owner')
        DeviceToken.objects.create(user=self.owner_user, token='OWNER_TOKEN')

        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION='Bearer ' + token(self.operator_user))
        self.c = c

        kapal = Kapal.objects.create(
            nama_kapal='KM Notif', jenis='Bagan', kapasitas=5)
        self.trip = Trip.objects.create(
            kapal=kapal, tgl_berangkat='2025-04-01', status='selesai')

    def tearDown(self):
        fcm_module._initialized = False

    @override_settings(**NO_FCM)
    def test_sync_sukses_buat_notifikasi(self):
        uid = str(uuid.uuid4())
        resp = self.c.post('/api/sync/', {'operations': [{
            'client_uuid': uid,
            'type': 'biaya',
            'data': {
                'trip': self.trip.id,
                'kategori': 'bbm',
                'jumlah': '300000',
            },
        }]}, format='json', **H)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['results'][0]['status'], 'synced')
        # Notification DB harus ada untuk owner
        self.assertEqual(
            Notification.objects.filter(user=self.owner_user, event='sync').count(), 1)

    @override_settings(**NO_FCM)
    def test_sync_duplikat_tidak_buat_notifikasi(self):
        uid = str(uuid.uuid4())
        payload = {'operations': [{
            'client_uuid': uid,
            'type': 'biaya',
            'data': {'trip': self.trip.id, 'kategori': 'es', 'jumlah': '100000'},
        }]}
        self.c.post('/api/sync/', payload, format='json', **H)   # pertama → synced
        Notification.objects.all().delete()                        # reset

        self.c.post('/api/sync/', payload, format='json', **H)   # kedua → duplicate
        self.assertEqual(Notification.objects.count(), 0)
