# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
"""Test pemisahan akses web portal: owner vs operator.

Skenario:
1. Operator diblokir dari halaman owner-only (master, laporan, bagi hasil)
2. Operator diarahkan ke daftar trip, bukan error 403
3. Operator tetap bisa akses halaman operasional (trip, tangkap, penjualan)
4. Owner bisa akses semua halaman
"""
from django.contrib.auth.models import User
from django.test import TestCase
from apps.api.models import UserProfile


class WebRoleAccessTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner_web', password='pass')
        UserProfile.objects.filter(user=self.owner).update(role='owner')

        self.operator = User.objects.create_user('operator_web', password='pass')
        UserProfile.objects.filter(user=self.operator).update(role='operator')

    # ── Operator diblokir dari halaman owner-only ──────────────────
    def test_operator_diblokir_dari_master(self):
        self.client.login(username='operator_web', password='pass')
        resp = self.client.get('/master/kapal/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/operasional/trip/', resp.url)

    def test_operator_diblokir_dari_laporan(self):
        self.client.login(username='operator_web', password='pass')
        resp = self.client.get('/laporan/')
        self.assertEqual(resp.status_code, 302)

    def test_operator_diblokir_dari_dashboard(self):
        self.client.login(username='operator_web', password='pass')
        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 302)

    # ── Operator tetap bisa akses operasional ──────────────────────
    def test_operator_bisa_akses_trip(self):
        self.client.login(username='operator_web', password='pass')
        resp = self.client.get('/operasional/trip/')
        self.assertEqual(resp.status_code, 200)

    # ── Owner bisa akses semua ─────────────────────────────────────
    def test_owner_bisa_akses_master(self):
        self.client.login(username='owner_web', password='pass')
        resp = self.client.get('/master/kapal/')
        self.assertEqual(resp.status_code, 200)

    def test_owner_bisa_akses_dashboard(self):
        self.client.login(username='owner_web', password='pass')
        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)

    def test_owner_bisa_akses_laporan(self):
        self.client.login(username='owner_web', password='pass')
        resp = self.client.get('/laporan/')
        self.assertEqual(resp.status_code, 200)
