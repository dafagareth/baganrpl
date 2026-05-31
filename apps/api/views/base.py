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

class _RefList(generics.ListAPIView):
    pagination_class = None

