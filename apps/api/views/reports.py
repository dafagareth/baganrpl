# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db.models import Sum, F, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.master.models import Kapal, ABK, JenisIkan, Pembeli
from apps.operasional.models import Trip, BiayaOperasional
from apps.tangkap.models import HasilTangkap
from apps.penjualan.models import Penjualan, BagiHasil

from ..models import DeviceToken, Notification
from ..permissions import IsOwner, IsOwnerOrReadOnly
from ..serializers import (
    RoleTokenObtainPairSerializer, MeSerializer, DeviceTokenSerializer,
    NotificationSerializer, KapalSerializer, ABKSerializer, JenisIkanSerializer,
    PembeliSerializer, TripSerializer, TripDetailSerializer,
    HasilTangkapSerializer, BagiHasilSerializer, TripCreateSerializer,
    BiayaRiwayatSerializer, HasilTangkapRiwayatSerializer, PenjualanRiwayatSerializer,
)

class DashboardView(APIView):
    def get(self, request):
        now = timezone.now()

        total_kapal = Kapal.objects.filter(status='aktif').count()
        trip_bulan_ini = Trip.objects.filter(
            tgl_berangkat__month=now.month, tgl_berangkat__year=now.year
        ).count()
        tangkap_bulan_ini = HasilTangkap.objects.filter(
            trip__tgl_berangkat__month=now.month,
            trip__tgl_berangkat__year=now.year,
        ).aggregate(total=Sum('berat_kg'))['total'] or 0
        pendapatan_bulan_ini = Penjualan.objects.filter(
            tgl_jual__month=now.month, tgl_jual__year=now.year
        ).aggregate(
            total=Sum(F('berat_terjual') * F('harga_per_kg'))
        )['total'] or 0
        biaya_bulan_ini = BiayaOperasional.objects.filter(
            trip__tgl_berangkat__month=now.month,
            trip__tgl_berangkat__year=now.year,
        ).aggregate(total=Sum('jumlah'))['total'] or 0
        laba_bulan_ini = float(pendapatan_bulan_ini) - float(biaya_bulan_ini)

        trip_terbaru = TripSerializer(
            Trip.objects.select_related('kapal').order_by('-dibuat_pada', '-id')[:5],
            many=True,
        ).data

        # Grafik 6 bulan terakhir
        chart = []
        nama_bulan = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                      'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']
        for i in range(5, -1, -1):
            d = date.today() - relativedelta(months=i)
            pendapatan = Penjualan.objects.filter(
                tgl_jual__month=d.month, tgl_jual__year=d.year
            ).aggregate(total=Sum(F('berat_terjual') * F('harga_per_kg')))['total'] or 0
            biaya = BiayaOperasional.objects.filter(
                trip__tgl_berangkat__month=d.month, trip__tgl_berangkat__year=d.year
            ).aggregate(total=Sum('jumlah'))['total'] or 0
            jumlah_trip = Trip.objects.filter(
                tgl_berangkat__month=d.month, tgl_berangkat__year=d.year
            ).count()
            chart.append({
                'label': f"{nama_bulan[d.month]}'{str(d.year)[2:]}",
                'pendapatan': float(pendapatan),
                'biaya': float(biaya),
                'laba': float(pendapatan) - float(biaya),
                'jumlah_trip': jumlah_trip,
            })

        # Komposisi tangkapan per jenis ikan (bulan ini, top 5)
        top_jenis_raw = (
            HasilTangkap.objects
            .filter(
                trip__tgl_berangkat__month=now.month,
                trip__tgl_berangkat__year=now.year,
            )
            .values('jenis_ikan__nama')
            .annotate(total_kg=Sum('berat_kg'))
            .order_by('-total_kg')[:5]
        )
        jenis_ikan_chart = [
            {'nama': item['jenis_ikan__nama'] or 'Tidak diketahui',
             'kg': float(item['total_kg'] or 0)}
            for item in top_jenis_raw
        ]

        # Top pembeli berdasarkan nilai penjualan (bulan ini, top 5)
        top_pembeli_raw = (
            Penjualan.objects
            .filter(tgl_jual__month=now.month, tgl_jual__year=now.year)
            .values('pembeli__nama')
            .annotate(total=Sum(F('berat_terjual') * F('harga_per_kg')))
            .order_by('-total')[:5]
        )
        pembeli_chart = [
            {'nama': item['pembeli__nama'] or 'Tanpa nama',
             'total': float(item['total'] or 0)}
            for item in top_pembeli_raw
        ]

        return Response({
            'total_kapal': total_kapal,
            'trip_bulan_ini': trip_bulan_ini,
            'tangkap_bulan_ini': float(tangkap_bulan_ini),
            'pendapatan_bulan_ini': float(pendapatan_bulan_ini),
            'biaya_bulan_ini': float(biaya_bulan_ini),
            'laba_bulan_ini': laba_bulan_ini,
            'trip_terbaru': trip_terbaru,
            'chart': chart,
            'jenis_ikan_chart': jenis_ikan_chart,
            'pembeli_chart': pembeli_chart,
        })

class LaporanChartsView(APIView):
    """Donut komposisi biaya + P&L 12 bulan."""
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        today = date.today()
        nama_bulan = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                      'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']

        # Donut: biaya per kategori (YTD tahun ini)
        KAT_LABEL = {
            'bbm': 'BBM', 'es': 'Es Balok', 'logistik': 'Logistik',
            'perawatan': 'Perawatan', 'lainnya': 'Lainnya',
        }
        biaya_kat_raw = (
            BiayaOperasional.objects
            .filter(trip__tgl_berangkat__year=today.year)
            .values('kategori')
            .annotate(total=Sum('jumlah'))
            .order_by('-total')
        )
        biaya_komposisi = [
            {
                'kategori': item['kategori'],
                'label': KAT_LABEL.get(item['kategori'], item['kategori'].title()),
                'total': float(item['total'] or 0),
            }
            for item in biaya_kat_raw
        ]

        # P&L 12 bulan + Margin trend (margin % per bulan, 6 bulan terakhir)
        pl_bulanan = []
        margin_trend = []
        for i in range(11, -1, -1):
            d = today - relativedelta(months=i)
            pendapatan = Penjualan.objects.filter(
                tgl_jual__month=d.month, tgl_jual__year=d.year
            ).aggregate(total=Sum(F('berat_terjual') * F('harga_per_kg')))['total'] or 0
            biaya = BiayaOperasional.objects.filter(
                trip__tgl_berangkat__month=d.month, trip__tgl_berangkat__year=d.year
            ).aggregate(total=Sum('jumlah'))['total'] or 0
            laba = float(pendapatan) - float(biaya)
            label = f"{nama_bulan[d.month]}'{str(d.year)[2:]}"
            pl_bulanan.append({
                'label': label,
                'laba': laba,
                'untung': laba >= 0,
            })
            if i <= 5:  # hanya 6 bulan terakhir untuk margin
                margin_pct = (laba / float(pendapatan) * 100) if pendapatan else 0
                margin_trend.append({
                    'label': label,
                    'margin_pct': round(margin_pct, 1),
                })

        # Laba per kapal (tahun berjalan) — bandingkan profitabilitas armada
        laba_per_kapal = []
        for kapal in Kapal.objects.filter(status__in=['aktif', 'perbaikan']):
            pendapatan_k = Penjualan.objects.filter(
                hasil_tangkap__trip__kapal=kapal,
                tgl_jual__year=today.year,
            ).aggregate(total=Sum(F('berat_terjual') * F('harga_per_kg')))['total'] or 0
            biaya_k = BiayaOperasional.objects.filter(
                trip__kapal=kapal,
                trip__tgl_berangkat__year=today.year,
            ).aggregate(total=Sum('jumlah'))['total'] or 0
            laba_k = float(pendapatan_k) - float(biaya_k)
            laba_per_kapal.append({
                'nama_kapal': kapal.nama_kapal,
                'laba': laba_k,
                'untung': laba_k >= 0,
            })
        laba_per_kapal.sort(key=lambda x: x['laba'], reverse=True)

        # Tren harga ikan rata-rata per kg (6 bulan) — indikator harga pasar
        harga_trend = []
        for i in range(5, -1, -1):
            d = today - relativedelta(months=i)
            avg_harga = Penjualan.objects.filter(
                tgl_jual__month=d.month, tgl_jual__year=d.year
            ).aggregate(rata=Avg('harga_per_kg'))['rata'] or 0
            harga_trend.append({
                'label': f"{nama_bulan[d.month]}'{str(d.year)[2:]}",
                'harga': float(avg_harga),
            })

        return Response({
            'biaya_komposisi': biaya_komposisi,
            'pl_bulanan': pl_bulanan,
            'margin_trend': margin_trend,
            'laba_per_kapal': laba_per_kapal,
            'harga_trend': harga_trend,
        })

class ArmadaChartsView(APIView):
    """Fleet utilization per kapal + tren volume vs trip 6 bulan."""
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        today = date.today()
        nama_bulan = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                      'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']
        bulan_ini = today.replace(day=1)
        hari_bulan = (bulan_ini + relativedelta(months=1) - bulan_ini).days

        # Fleet utilization: hitung hari aktif tiap kapal bulan ini
        kapal_list = Kapal.objects.filter(status__in=['aktif', 'perbaikan'])
        utilisasi = []
        for kapal in kapal_list:
            trips = Trip.objects.filter(
                kapal=kapal,
                tgl_berangkat__month=today.month,
                tgl_berangkat__year=today.year,
            ).exclude(status='batal')
            hari_aktif = 0
            for t in trips:
                start = t.tgl_berangkat
                end = t.tgl_kembali if t.tgl_kembali else today
                hari_aktif += max(0, (end - start).days + 1)
            hari_aktif = min(hari_aktif, hari_bulan)
            utilisasi.append({
                'nama_kapal': kapal.nama_kapal,
                'hari_aktif': hari_aktif,
                'hari_bersandar': hari_bulan - hari_aktif,
                'total_hari': hari_bulan,
            })

        # Tren volume tangkapan (kg) vs jumlah trip — 6 bulan
        tren = []
        for i in range(5, -1, -1):
            d = today - relativedelta(months=i)
            total_kg = HasilTangkap.objects.filter(
                trip__tgl_berangkat__month=d.month,
                trip__tgl_berangkat__year=d.year,
            ).aggregate(total=Sum('berat_kg'))['total'] or 0
            jumlah_trip = Trip.objects.filter(
                tgl_berangkat__month=d.month,
                tgl_berangkat__year=d.year,
            ).exclude(status='batal').count()
            tren.append({
                'label': f"{nama_bulan[d.month]}'{str(d.year)[2:]}",
                'total_kg': float(total_kg),
                'jumlah_trip': jumlah_trip,
            })

        return Response({
            'utilisasi_kapal': utilisasi,
            'tren_bulanan': tren,
        })

class MapLokasiView(APIView):
    """Titik-titik lokasi trip (hanya trip yang menyimpan koordinat GPS)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trips = (
            Trip.objects.select_related('kapal')
            .filter(lat__isnull=False, lng__isnull=False)
            .exclude(status='batal')
            .order_by('-tgl_berangkat')
        )
        data = []
        for t in trips:
            data.append({
                'id': t.id,
                'kapal_nama': t.kapal.nama_kapal,
                'tgl_berangkat': t.tgl_berangkat.isoformat(),
                'status': t.status,
                'lat': float(t.lat),
                'lng': float(t.lng),
            })
        return Response({'lokasi': data})

