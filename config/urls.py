# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
#
# Daftar URL teratas (papan saklar). Tiap request dicocokkan dari atas ke bawah:
# URL spesifik (login, dashboard, halaman legal) ditangani langsung di sini; URL yang
# diawali nama app (master/, operasional/, dst) dilempar ke urls.py app itu via include().
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.core.views import CustomLoginView, DashboardView, PublicHomeView
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', PublicHomeView.as_view(), name='home'),
    path('privasi/', TemplateView.as_view(template_name='legal/privasi.html'), name='privasi'),
    path('syarat/', TemplateView.as_view(template_name='legal/syarat.html'), name='syarat'),
    path('disclaimer/', TemplateView.as_view(template_name='legal/disclaimer.html'), name='disclaimer'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('master/', include('apps.master.urls')),
    path('operasional/', include('apps.operasional.urls')),
    path('tangkap/', include('apps.tangkap.urls')),
    path('penjualan/', include('apps.penjualan.urls')),
    path('laporan/', include('apps.laporan.urls')),
    # REST API (untuk app Flutter) — dinonaktifkan, proyek fokus web.
    # Aktifkan lagi (beserta rest_framework & corsheaders di settings) bila mobile dilanjut.
    # path('api/', include('apps.api.urls')),
]

admin.site.site_header = 'Sistem Informasi Usaha Bagan'
admin.site.site_title = 'SI Usaha Bagan'
admin.site.index_title = 'Panel Administrasi'

# Media (foto bukti). Di dev dilayani static(); di produksi (DEBUG=False) tetap
# dilayani via Django serve() — cukup untuk trafik demo. Skala besar: pakai Caddy/Nginx.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    from django.urls import re_path
    from django.views.static import serve as _media_serve
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', _media_serve, {'document_root': settings.MEDIA_ROOT}),
    ]