# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.urls import path
from . import views

app_name = 'laporan'

urlpatterns = [
    path('', views.LaporanIndexView.as_view(), name='index'),
    path('export/excel/', views.ExportExcelView.as_view(), name='export_excel'),
]