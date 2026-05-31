# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .sync import SyncView

app_name = 'api'

urlpatterns = [
    # Auth
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('me/', views.MeView.as_view(), name='me'),
    path('me/foto/', views.MeFotoView.as_view(), name='me_foto'),
    path('devices/', views.RegisterDeviceView.as_view(), name='register_device'),

    # Notifikasi (inbox)
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-read/', views.MarkNotificationsReadView.as_view(), name='mark_read'),

    # Master Data (GET list + POST create; owner write, all read)
    path('kapal/', views.KapalListCreateView.as_view(), name='kapal'),
    path('kapal/<int:pk>/', views.KapalDetailView.as_view(), name='kapal_detail'),
    path('kapal/<int:pk>/foto/', views.KapalFotoView.as_view(), name='kapal_foto'),
    path('kapal/<int:pk>/operators/', views.KapalOperatorView.as_view(), name='kapal_operators'),
    path('kapal/<int:pk>/operators/<int:uid>/', views.KapalOperatorView.as_view(), name='kapal_operator_detail'),
    path('abk/tersedia/', views.ABKTersediaView.as_view(), name='abk_tersedia'),
    path('abk/', views.ABKListCreateView.as_view(), name='abk'),
    path('abk/<int:pk>/', views.ABKDetailView.as_view(), name='abk_detail'),
    path('jenis-ikan/', views.JenisIkanListCreateView.as_view(), name='jenis_ikan'),
    path('jenis-ikan/<int:pk>/', views.JenisIkanDetailView.as_view(), name='jenis_ikan_detail'),
    path('pembeli/', views.PembeliListCreateView.as_view(), name='pembeli'),
    path('pembeli/<int:pk>/', views.PembeliDetailView.as_view(), name='pembeli_detail'),
    # Riwayat input operator (server history, persistent)
    path('biaya/', views.BiayaListView.as_view(), name='biaya_list'),
    path('biaya/<int:pk>/', views.BiayaDetailView.as_view(), name='biaya_detail'),
    path('hasil-tangkap/semua/', views.HasilTangkapSemuaView.as_view(), name='hasil_tangkap_semua'),
    path('hasil-tangkap/<int:pk>/', views.HasilTangkapDetailView.as_view(), name='ht_detail'),
    path('penjualan/', views.PenjualanListView.as_view(), name='penjualan_list'),
    path('penjualan/<int:pk>/', views.PenjualanDetailView.as_view(), name='penjualan_detail'),

    path('trips/', views.TripListView.as_view(), name='trips'),
    path('trips/create/', views.TripCreateView.as_view(), name='trip_create'),
    path('trips/<int:pk>/', views.TripDetailView.as_view(), name='trip_detail'),
    path('trips/<int:pk>/kunci-laporan/', views.KunciLaporanView.as_view(), name='kunci_laporan'),
    path('trips/<int:trip_id>/bagi-hasil/', views.BagiHasilListCreateView.as_view(), name='bagi_hasil_list'),
    path('hasil-tangkap/', views.HasilTangkapTersediaView.as_view(), name='hasil_tangkap'),

    # Bagi hasil per-item (owner)
    path('bagi-hasil/<int:pk>/', views.BagiHasilDetailView.as_view(), name='bagi_hasil_detail'),

    # Dashboard owner
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('laporan-charts/', views.LaporanChartsView.as_view(), name='laporan_charts'),
    path('armada-charts/', views.ArmadaChartsView.as_view(), name='armada_charts'),
    path('map-lokasi/', views.MapLokasiView.as_view(), name='map_lokasi'),

    # Manajemen akun operator (owner only)
    path('accounts/', views.OperatorAccountListCreateView.as_view(), name='accounts'),
    path('accounts/<int:pk>/', views.OperatorAccountDetailView.as_view(), name='account_detail'),
    path('accounts/<int:pk>/reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),

    # Sinkronisasi offline (outbox dari Flutter)
    path('sync/', SyncView.as_view(), name='sync'),
]
