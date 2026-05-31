# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.urls import path
from . import views

app_name = 'tangkap'

urlpatterns = [
    path('', views.HasilTangkapListView.as_view(), name='list'),
    path('trip/<int:trip_id>/tambah/', views.HasilTangkapCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.HasilTangkapUpdateView.as_view(), name='update'),
    path('<int:pk>/hapus/', views.HasilTangkapDeleteView.as_view(), name='delete'),
]