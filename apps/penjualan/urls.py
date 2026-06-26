# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
#
# Daftar URL app penjualan. app_name + name tiap path dipakai untuk memanggil URL dari
# kode/template, mis. {% url 'penjualan:bagi_hasil_list' %}. <int:trip_id> menangkap
# angka dari alamat lalu dikirim ke view sebagai argumen.
from django.urls import path
from . import views

app_name = 'penjualan'

urlpatterns = [
    # Penjualan
    path('', views.PenjualanListView.as_view(), name='list'),
    path('tambah/', views.PenjualanCreateView.as_view(), name='create'),
    path('trip/<int:trip_id>/tambah/', views.PenjualanCreateForTripView.as_view(), name='create_for_trip'),
    path('tambah-banyak/', views.penjualan_multi_create, name='create_multi'),
    path('<int:pk>/edit/', views.PenjualanUpdateView.as_view(), name='update'),
    path('<int:pk>/hapus/', views.PenjualanDeleteView.as_view(), name='delete'),

    # Bagi Hasil
    path('bagi-hasil/', views.BagiHasilListView.as_view(), name='bagi_hasil_list'),
    path('bagi-hasil/tambah/', views.BagiHasilCreateGlobalView.as_view(), name='bagi_hasil_create_global'),
    path('bagi-hasil/trip/<int:trip_id>/tambah/', views.BagiHasilCreateView.as_view(), name='bagi_hasil_create'),
    path('bagi-hasil/trip/<int:trip_id>/tambah-banyak/', views.BagiHasilMultiCreateView.as_view(), name='bagi_hasil_multi_create'),
    path('bagi-hasil/<int:pk>/edit/', views.BagiHasilUpdateView.as_view(), name='bagi_hasil_update'),
    path('bagi-hasil/<int:pk>/lunas/', views.bagi_hasil_mark_paid, name='bagi_hasil_mark_paid'),
]