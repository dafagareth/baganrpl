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

class KapalListCreateView(generics.ListCreateAPIView):
    serializer_class = KapalSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if profile and profile.role == 'operator':
            # Operator hanya melihat kapal yang ditugaskan padanya
            assigned = OperatorKapal.objects.filter(operator=user).values_list('kapal_id', flat=True)
            return Kapal.objects.filter(id__in=assigned)
        return Kapal.objects.all()

class KapalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = KapalSerializer
    queryset = Kapal.objects.all()
    permission_classes = [IsAuthenticated, IsOwner]

class KapalFotoView(APIView):
    """POST /api/kapal/{id}/foto/ — upload/ganti foto profil kapal (owner only)."""
    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request, pk):
        kapal = get_object_or_404(Kapal, pk=pk)
        foto = request.FILES.get('foto')
        if not foto:
            return Response({'detail': 'File foto wajib dikirim.'}, status=400)
        if kapal.foto:
            kapal.foto.delete(save=False)
        kapal.foto.save(foto.name, foto, save=True)
        return Response(KapalSerializer(kapal, context={'request': request}).data)

    def delete(self, request, pk):
        kapal = get_object_or_404(Kapal, pk=pk)
        if kapal.foto:
            kapal.foto.delete(save=True)
        return Response(status=204)

class ABKListCreateView(generics.ListCreateAPIView):
    serializer_class = ABKSerializer
    queryset = ABK.objects.all()   # semua ABK (termasuk nonaktif) untuk CRUD
    pagination_class = None
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

class ABKDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ABKSerializer
    queryset = ABK.objects.all()
    permission_classes = [IsAuthenticated, IsOwner]

class JenisIkanListCreateView(generics.ListCreateAPIView):
    serializer_class = JenisIkanSerializer
    queryset = JenisIkan.objects.all()
    pagination_class = None
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

class JenisIkanDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JenisIkanSerializer
    queryset = JenisIkan.objects.all()
    permission_classes = [IsAuthenticated, IsOwner]

class PembeliListCreateView(generics.ListCreateAPIView):
    serializer_class = PembeliSerializer
    queryset = Pembeli.objects.all()
    pagination_class = None
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

class PembeliDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PembeliSerializer
    queryset = Pembeli.objects.all()
    permission_classes = [IsAuthenticated, IsOwner]

