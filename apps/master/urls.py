# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.urls import path
from . import views

app_name = 'master'

urlpatterns = [
    path('', views.DataMasterIndexView.as_view(), name='index'),

    # Kapal
    path('kapal/', views.KapalListView.as_view(), name='kapal_list'),
    path('kapal/tambah/', views.KapalCreateView.as_view(), name='kapal_create'),
    path('kapal/<int:pk>/edit/', views.KapalUpdateView.as_view(), name='kapal_update'),
    path('kapal/<int:pk>/hapus/', views.KapalDeleteView.as_view(), name='kapal_delete'),

    # ABK
    path('abk/', views.ABKListView.as_view(), name='abk_list'),
    path('abk/tambah/', views.ABKCreateView.as_view(), name='abk_create'),
    path('abk/<int:pk>/edit/', views.ABKUpdateView.as_view(), name='abk_update'),
    path('abk/<int:pk>/hapus/', views.ABKDeleteView.as_view(), name='abk_delete'),

    # Jenis Ikan
    path('ikan/', views.JenisIkanListView.as_view(), name='ikan_list'),
    path('ikan/tambah/', views.JenisIkanCreateView.as_view(), name='ikan_create'),
    path('ikan/<int:pk>/edit/', views.JenisIkanUpdateView.as_view(), name='ikan_update'),
    path('ikan/<int:pk>/hapus/', views.JenisIkanDeleteView.as_view(), name='ikan_delete'),

    # Pembeli
    path('pembeli/', views.PembeliListView.as_view(), name='pembeli_list'),
    path('pembeli/tambah/', views.PembeliCreateView.as_view(), name='pembeli_create'),
    path('pembeli/<int:pk>/edit/', views.PembeliUpdateView.as_view(), name='pembeli_update'),
    path('pembeli/<int:pk>/hapus/', views.PembeliDeleteView.as_view(), name='pembeli_delete'),
]