# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.urls import path
from .views import LaporanIndexView
from .views_export import ExportExcelView, ExportPDFTripView

app_name = 'laporan'

urlpatterns = [
    path('', LaporanIndexView.as_view(), name='index'),
    path('export/excel/', ExportExcelView.as_view(), name='export_excel'),
    path('trip/<int:pk>/pdf/', ExportPDFTripView.as_view(), name='export_pdf_trip'),
]