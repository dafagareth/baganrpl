# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.urls import path
from . import views

app_name = 'operasional'

urlpatterns = [
    path('trip/', views.TripListView.as_view(), name='trip_list'),
    path('trip/tambah/', views.TripCreateView.as_view(), name='trip_create'),
    path('trip/<int:pk>/', views.TripDetailView.as_view(), name='trip_detail'),
    path('trip/<int:pk>/edit/', views.TripUpdateView.as_view(), name='trip_update'),
    path('trip/<int:pk>/hapus/', views.TripDeleteView.as_view(), name='trip_delete'),
    path('trip/<int:trip_id>/biaya/tambah/', views.BiayaCreateView.as_view(), name='biaya_create'),
    path('biaya/<int:pk>/hapus/', views.BiayaDeleteView.as_view(), name='biaya_delete'),
    path('trip/<int:trip_id>/abk/tambah/', views.TripAddABKView.as_view(), name='trip_add_abk'),
    path('trip/<int:trip_id>/abk/<int:abk_id>/hapus/', views.TripRemoveABKView.as_view(), name='trip_remove_abk'),
]