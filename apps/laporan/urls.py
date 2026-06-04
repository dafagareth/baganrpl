# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.urls import path
from . import views

app_name = 'laporan'

urlpatterns = [
    path('', views.LaporanIndexView.as_view(), name='index'),
    path('export/excel/', views.ExportExcelView.as_view(), name='export_excel'),
    path('trip/<int:pk>/pdf/', views.ExportPDFTripView.as_view(), name='export_pdf_trip'),
]