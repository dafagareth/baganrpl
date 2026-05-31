# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.master.views import DashboardView, PublicHomeView
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
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
    path('api/', include('apps.api.urls')),
]

admin.site.site_header = 'Sistem Informasi Usaha Bagan'
admin.site.site_title = 'SI Usaha Bagan'
admin.site.index_title = 'Panel Administrasi'

# Serve media files in development (foto bukti penjualan, dll)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)