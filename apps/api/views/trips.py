# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
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

from apps.master.models import Kapal, ABK, JenisIkan, Pembeli, OperatorKapal
from apps.operasional.models import Trip, TripABK, BiayaOperasional
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

from .base import _RefList

class TripListView(_RefList):
    serializer_class = TripSerializer
    queryset = Trip.objects.select_related('kapal').prefetch_related(
        'biaya_operasional',
        'hasil_tangkap__penjualan',
    ).order_by('-dibuat_pada', '-id')

class TripCreateView(APIView):
    """Buat trip baru — boleh oleh operator maupun owner."""
    def post(self, request):
        from ..fcm import notify_owners
        serializer = TripCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        kapal = serializer.validated_data['kapal']
        profile = getattr(request.user, 'profile', None)

        # Operator wajib di-assign ke kapal yang dipilih
        if profile and profile.role == 'operator':
            if not OperatorKapal.objects.filter(operator=request.user, kapal=kapal).exists():
                return Response(
                    {'detail': 'Anda tidak ditugaskan ke kapal ini.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Proses ABK: auto-pindah yang sedang di trip 'persiapan', blokir yang 'berlayar'
        abk_ids = serializer.validated_data.get('abk_ids', [])
        dipindahkan = []
        for abk_id in abk_ids:
            existing = TripABK.objects.filter(
                abk_id=abk_id, trip__status__in=['persiapan', 'berlayar']
            ).select_related('trip__kapal').first()
            if existing:
                if existing.trip.status == 'berlayar':
                    abk = ABK.objects.get(pk=abk_id)
                    return Response(
                        {'detail': f'ABK {abk.nama} sedang berlayar di kapal '
                                   f'{existing.trip.kapal.nama_kapal} — tidak bisa dipindahkan.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # status 'persiapan' → pindahkan
                dipindahkan.append({
                    'abk_id': abk_id,
                    'dari_trip_id': existing.trip_id,
                    'dari_kapal': existing.trip.kapal.nama_kapal,
                })
                existing.delete()

        trip = serializer.save(dibuat_oleh=request.user)

        operator_name = request.user.get_full_name() or request.user.username
        tgl = trip.tgl_berangkat.strftime('%-d %b %Y') if trip.tgl_berangkat else '-'
        notify_owners(
            event='trip_baru',
            judul=f'Trip Baru — {trip.kapal.nama_kapal}',
            pesan=f'{operator_name} membuat trip, berangkat {tgl}',
            data={'trip_id': trip.id},
        )
        resp = TripSerializer(trip).data
        resp['abk_dipindahkan'] = dipindahkan
        return Response(resp, status=status.HTTP_201_CREATED)

class HasilTangkapTersediaView(_RefList):
    """Hasil tangkap yang masih punya stok untuk dijual."""
    serializer_class = HasilTangkapSerializer

    def get_queryset(self):
        qs = HasilTangkap.objects.select_related('trip__kapal', 'jenis_ikan')
        return [ht for ht in qs if ht.berat_tersedia > 0]

class TripDetailView(APIView):
    """
    GET   /api/trips/{id}/  — detail keuangan + ABK (owner & operator)
    PATCH /api/trips/{id}/  — ubah status / tgl_kembali / catatan (owner & operator)
    """

    def get(self, request, pk):
        trip = get_object_or_404(
            Trip.objects.select_related('kapal').prefetch_related(
                'trip_abk__abk', 'bagi_hasil'),
            pk=pk,
        )
        return Response(TripDetailSerializer(trip, context={'request': request}).data)

    def patch(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk)
        # Hanya field aman yang boleh diubah via endpoint ini
        allowed = {'status', 'tgl_kembali', 'catatan'}
        for field, value in request.data.items():
            if field in allowed:
                setattr(trip, field, value if value != '' else None)
        trip.save()
        return Response(TripSerializer(trip).data)

class KunciLaporanView(APIView):
    """POST /api/trips/{pk}/kunci-laporan/ — kunci laporan trip (owner only).

    Setelah dikunci, tangkap & penjualan tidak bisa diedit/dihapus operator.
    Biaya sudah terkunci otomatis saat trip berstatus 'selesai'.
    Lock bersifat permanen — tidak bisa dibuka kembali via API ini.
    """
    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk)
        if trip.status != 'selesai':
            return Response(
                {'detail': 'Laporan hanya bisa dikunci untuk trip yang sudah selesai.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if trip.is_laporan_locked:
            return Response(
                {'detail': 'Laporan sudah dikunci sebelumnya.'},
                status=status.HTTP_200_OK,
            )
        trip.is_laporan_locked = True
        trip.save(update_fields=['is_laporan_locked'])
        return Response({'detail': 'Laporan berhasil dikunci.', 'is_laporan_locked': True})

