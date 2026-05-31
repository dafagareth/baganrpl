# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.operasional.models import BiayaOperasional
from apps.tangkap.models import HasilTangkap
from apps.penjualan.models import Penjualan

from ..serializers import (
    BiayaRiwayatSerializer,
    HasilTangkapRiwayatSerializer,
    PenjualanRiwayatSerializer,
)


class BiayaListView(generics.ListAPIView):
    """Riwayat semua biaya operasional — untuk history tiap operator."""
    serializer_class = BiayaRiwayatSerializer
    pagination_class = None

    def get_queryset(self):
        return BiayaOperasional.objects.select_related(
            'trip__kapal'
        ).order_by('-dibuat_pada', '-id')


class HasilTangkapSemuaView(generics.ListAPIView):
    """Semua hasil tangkap (tidak filter stok) — untuk history operator."""
    serializer_class = HasilTangkapRiwayatSerializer
    pagination_class = None

    def get_queryset(self):
        return HasilTangkap.objects.select_related(
            'trip__kapal', 'jenis_ikan'
        ).order_by('-dibuat_pada', '-id')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PenjualanListView(generics.ListAPIView):
    serializer_class = PenjualanRiwayatSerializer
    pagination_class = None

    def get_queryset(self):
        return Penjualan.objects.select_related(
            'hasil_tangkap__trip__kapal',
            'hasil_tangkap__jenis_ikan',
            'pembeli',
        ).order_by('-dibuat_pada', '-id')


class BiayaDetailView(APIView):
    """PATCH & DELETE satu entri biaya operasional milik operator yang login."""
    permission_classes = [IsAuthenticated]

    def _get_obj(self, pk, user):
        return get_object_or_404(
            BiayaOperasional.objects.select_related('trip__kapal'),
            pk=pk,
        )

    def patch(self, request, pk):
        obj = self._get_obj(pk, request.user)
        if obj.trip.status == 'selesai':
            raise PermissionDenied('Biaya tidak bisa diubah — trip sudah selesai.')
        for field in ('kategori', 'jumlah', 'keterangan'):
            if field in request.data:
                setattr(obj, field, request.data[field])
        obj.save()
        return Response(BiayaRiwayatSerializer(obj).data)

    def delete(self, request, pk):
        obj = self._get_obj(pk, request.user)
        if obj.trip.status == 'selesai':
            raise PermissionDenied('Biaya tidak bisa dihapus — trip sudah selesai.')
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HasilTangkapDetailView(APIView):
    """PATCH & DELETE satu entri hasil tangkap milik operator yang login."""
    permission_classes = [IsAuthenticated]

    def _get_obj(self, pk, user):
        return get_object_or_404(
            HasilTangkap.objects.select_related('trip__kapal', 'jenis_ikan'),
            pk=pk,
        )

    def patch(self, request, pk):
        obj = self._get_obj(pk, request.user)
        if obj.trip.is_laporan_locked:
            raise PermissionDenied('Hasil tangkap tidak bisa diubah — laporan trip sudah dikunci.')
        for field in ('jenis_ikan_id', 'berat_kg', 'kondisi', 'catatan'):
            key = 'jenis_ikan' if field == 'jenis_ikan_id' else field
            if key in request.data:
                setattr(obj, field, request.data[key])
        obj.save()
        return Response(HasilTangkapRiwayatSerializer(obj, context={'request': request}).data)

    def delete(self, request, pk):
        obj = self._get_obj(pk, request.user)
        if obj.trip.is_laporan_locked:
            raise PermissionDenied('Hasil tangkap tidak bisa dihapus — laporan trip sudah dikunci.')
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PenjualanDetailView(APIView):
    """PATCH & DELETE satu entri penjualan milik operator yang login."""
    permission_classes = [IsAuthenticated]

    def _get_obj(self, pk, user):
        return get_object_or_404(
            Penjualan.objects.select_related(
                'hasil_tangkap__trip__kapal', 'hasil_tangkap__jenis_ikan', 'pembeli'),
            pk=pk,
        )

    def patch(self, request, pk):
        obj = self._get_obj(pk, request.user)
        if obj.hasil_tangkap.trip.is_laporan_locked:
            raise PermissionDenied('Penjualan tidak bisa diubah — laporan trip sudah dikunci.')
        for field in ('jenis_ikan_id', 'pembeli_id', 'berat_terjual',
                      'harga_per_kg', 'tgl_jual', 'catatan'):
            key = {'jenis_ikan_id': 'jenis_ikan', 'pembeli_id': 'pembeli'}.get(field, field)
            if key in request.data:
                setattr(obj, field, request.data[key])
        obj.save()
        return Response(PenjualanRiwayatSerializer(obj, context={'request': request}).data)

    def delete(self, request, pk):
        obj = self._get_obj(pk, request.user)
        if obj.hasil_tangkap.trip.is_laporan_locked:
            raise PermissionDenied('Penjualan tidak bisa dihapus — laporan trip sudah dikunci.')
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
