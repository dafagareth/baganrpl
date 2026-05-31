# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.urls import path
from . import views

app_name = 'penjualan'

urlpatterns = [
    # Penjualan
    path('', views.PenjualanListView.as_view(), name='list'),
    path('tambah/', views.PenjualanCreateView.as_view(), name='create'),
    path('tambah-banyak/', views.penjualan_multi_create, name='create_multi'),
    path('<int:pk>/edit/', views.PenjualanUpdateView.as_view(), name='update'),
    path('<int:pk>/hapus/', views.PenjualanDeleteView.as_view(), name='delete'),

    # Bagi Hasil
    path('bagi-hasil/', views.BagiHasilListView.as_view(), name='bagi_hasil_list'),
    path('bagi-hasil/tambah/', views.BagiHasilCreateGlobalView.as_view(), name='bagi_hasil_create_global'),
    path('bagi-hasil/trip/<int:trip_id>/tambah/', views.BagiHasilCreateView.as_view(), name='bagi_hasil_create'),
    path('bagi-hasil/<int:pk>/edit/', views.BagiHasilUpdateView.as_view(), name='bagi_hasil_update'),
]