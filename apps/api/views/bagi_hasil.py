# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.operasional.models import Trip
from apps.penjualan.models import BagiHasil

from ..permissions import IsOwner
from ..serializers import BagiHasilSerializer


class BagiHasilListCreateView(APIView):
    """
    GET  /api/trips/{id}/bagi-hasil/  → list semua bagi hasil trip ini
    POST /api/trips/{id}/bagi-hasil/  → tambah bagi hasil (owner only)
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]

    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        qs = BagiHasil.objects.filter(trip=trip).select_related('abk')
        return Response(BagiHasilSerializer(qs, many=True).data)

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        # Sisipkan trip dari URL agar tidak bisa di-forge dari body
        data = {**request.data, 'trip': trip.id}
        serializer = BagiHasilSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(BagiHasilSerializer(obj).data, status=status.HTTP_201_CREATED)


class BagiHasilDetailView(APIView):
    """
    PATCH  /api/bagi-hasil/{id}/  → ubah nominal / tandai sudah_dibayar (owner only)
    DELETE /api/bagi-hasil/{id}/  → hapus (owner only)
    """
    permission_classes = [IsAuthenticated, IsOwner]

    def _get_obj(self, pk):
        return get_object_or_404(BagiHasil.objects.select_related('abk', 'trip'), pk=pk)

    def patch(self, request, pk):
        obj = self._get_obj(pk)
        serializer = BagiHasilSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(BagiHasilSerializer(obj).data)

    def delete(self, request, pk):
        obj = self._get_obj(pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
